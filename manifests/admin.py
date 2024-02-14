from typing import List
from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
from django.urls.resolvers import URLPattern
from django.core.exceptions import ValidationError
import csv
from io import StringIO
import nested_admin
from .models import *
import requests
import pandas as pd
import sage_data_client


# Register your models here.
class ResourceInline(nested_admin.NestedStackedInline):
    model = Resource
    extra = 0
    fk_name = "node"


class ComputeSensorInline(nested_admin.NestedStackedInline):
    model = ComputeSensor
    extra = 0
    fk_name = "scope"


class ComputeInline(nested_admin.NestedStackedInline):
    model = Compute
    extra = 0
    fk_name = "node"
    inlines = [ComputeSensorInline]


class NodeSensorInline(nested_admin.NestedStackedInline):
    model = NodeSensor
    extra = 0
    fk_name = "node"


class ModemInline(nested_admin.NestedStackedInline):
    model = Modem
    fk_name = "node"
    extra = 0


@admin.register(NodeData)
class NodeAdmin(nested_admin.NestedModelAdmin):
    # display in admin panel
    list_display = (
        "vsn",
        "name",
        "phase",
        "project",
        "focus",
        "address",
        "gps_lat",
        "gps_lon",
        "get_computes",
        "registered_at",
    )
    list_filter = ("phase", "project", "registered_at")
    search_fields = ("vsn", "name", "phase", "notes", "location", "compute__name")
    ordering = ("vsn",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "vsn",
                    "name",
                    "phase",
                    "project",
                    "partner",
                    "focus",
                    "notes",
                    "tags",
                    "registered_at",
                )
            },
        ),
        ("Location", {"fields": ("location", "address", "gps_lat", "gps_lon")}),
    )

    inlines = [ModemInline, ComputeInline, NodeSensorInline, ResourceInline]

    def address_info(self, obj):
        if obj.address:
            return f"{obj.address.street_address}, {obj.address.city}, {obj.address.country}"
        return "No address"

    address_info.short_description = 'Address'

    actions = ["autopopulate_from_beekeeper_and_data", "export_as_json"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "modem",
                "tags",
                "computes",
            )
        )

    @admin.display(description="Tags")
    def get_tags(self, obj):
        return ",".join(obj.tags.values_list("tag", flat=True).order_by("tag"))

    @admin.display(description="Computes")
    def get_computes(self, obj):
        return ",".join(obj.compute_set.values_list("name", flat=True).order_by("name"))

    @admin.action(description="Autopopulate nodes using beekeeper and data")
    def autopopulate_from_beekeeper_and_data(self, request, queryset):
        r = requests.get("https://api.sagecontinuum.org/api/state", timeout=5)
        r.raise_for_status()

        # get latest beekeeper state by vsn
        df = pd.DataFrame(r.json()["data"])
        df.rename(columns={"id": "node_id"}, inplace=True)
        df["registration_event"] = pd.to_datetime(df["registration_event"], utc=True)
        df = df[["vsn", "node_id", "registration_event"]]
        latest_state = df.groupby("vsn").apply(
            lambda df: df.loc[df["registration_event"].idxmax()]
        )

        # get recently publishing devices
        df = sage_data_client.query(start="-1h", tail=1, filter={"name": "sys.uptime"})
        df.rename(columns={"meta.vsn": "vsn", "meta.host": "host"}, inplace=True)
        df[["serial_no", "device"]] = df["host"].str.extract(r"^([0-9a-f]+)\.(.*)$")
        df["serial_no"] = df["serial_no"].str.upper().str[-12:]
        uptimes = df[["vsn", "serial_no", "device", "timestamp"]]

        # TODO(sean) how to handle adding extra devices if recently swapped?
        # TODO(sean) what we probably should do is actually have the node publish
        # a discovered manifest periodically. then we can use this to populate this

        sbcore_hw = ComputeHardware.objects.get(hardware="dell-xr2")
        nxcore_hw = ComputeHardware.objects.get(hardware="xaviernx")
        nxagent_hw = ComputeHardware.objects.get(hardware="xaviernx-poe")
        rpi_hw = ComputeHardware.objects.get(hardware="rpi-8gb")

        for node in queryset:
            node: NodeData
            try:
                r = latest_state.loc[node.vsn]
            except KeyError:
                continue

            try:
                build = NodeBuild.objects.get(vsn=node.vsn)
            except NodeBuild.DoesNotExist:
                continue

            if (
                    node.registered_at is None
                    or (r.registration_event > node.registered_at)
                    or (
                    r.registration_event >= node.registered_at
                    and r.node_id != node.name
            )
            ):
                node.registered_at = r.registration_event
                node.name = r.node_id
                node.save()

            # filter for the n most recent items depending on device
            node_uptimes = uptimes[uptimes.vsn == node.vsn]
            num_rpis = int(build.shield) + int(build.extra_rpi)
            num_agents = int(build.agent)
            latest_uptimes = pd.concat(
                [
                    node_uptimes[node_uptimes.device == "sb-core"]
                    .sort_values("timestamp")
                    .tail(1),
                    node_uptimes[node_uptimes.device == "ws-nxcore"]
                    .sort_values("timestamp")
                    .tail(1),
                    node_uptimes[node_uptimes.device == "ws-nxagent"]
                    .sort_values("timestamp")
                    .tail(num_agents),
                    node_uptimes[node_uptimes.device == "ws-rpi"]
                    .sort_values("timestamp")
                    .tail(num_rpis),
                ]
            )

            for r in latest_uptimes.itertuples():
                if r.device == "sb-core":
                    name = "sbcore"
                    hardware = sbcore_hw
                    zone = "core"
                elif r.device == "ws-nxcore":
                    name = "nxcore"
                    hardware = nxcore_hw
                    zone = "core"
                elif r.device == "ws-nxagent":
                    name = "nxagent"
                    hardware = nxagent_hw
                    zone = "agent"
                elif r.device == "ws-rpi":
                    name = "rpi"
                    hardware = rpi_hw
                    zone = "shield" if build.shield and not build.extra_rpi else None
                else:
                    # TODO alert admin of unknown device type
                    continue

                # create compute if needed and update unset fields
                try:
                    compute = node.compute_set.get(serial_no=r.serial_no)
                    if not compute.name:
                        compute.name = name
                    if not compute.hardware:
                        compute.hardware = hardware
                    if not compute.zone:
                        compute.zone = zone
                    compute.save()
                except Compute.DoesNotExist:
                    compute = node.compute_set.create(
                        name=name,
                        hardware=hardware,
                        serial_no=r.serial_no,
                        zone=zone,
                    )

            # add default devices when possible too
            add_default_devices_using_zone(self, request, node.compute_set.all())

    @admin.action(description="Export as JSON")
    def export_as_json(self, request, queryset):
        response = HttpResponse(content_type="application/json")
        serializers.serialize(
            "json", queryset, stream=response, use_natural_foreign_keys=True
        )
        return response


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(Modem)
class ModemAdmin(admin.ModelAdmin):
    list_display = ["imei", "imsi", "iccid", "node", "sim_type", "model"]
    list_filter = ["sim_type", "model", "carrier"]
    search_fields = ["imei", "imsi", "iccid", "node__vsn", "sim_type"]
    autocomplete_fields = ["node"]

    change_list_template = "manifests/modem_change_list.html"

    def get_urls(self) -> List[URLPattern]:
        urls = super().get_urls()
        extra_urls = [
            path("upload-csv/", self.admin_site.admin_view(self.upload_csv)),
        ]
        return extra_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        extra["csv_upload_form"] = CSVUploadForm()
        return super().changelist_view(request, extra_context=extra)

    def upload_csv(self, request):
        if request.method != "POST":
            return redirect("..")

        form = CSVUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            self.message_user(request, "Error getting form data!", level=messages.ERROR)
            return redirect("..")

        if not request.FILES["csv_file"].name.endswith("csv"):
            self.message_user(request, "File must be a CSV!", level=messages.ERROR)
            return redirect("..")

        decoded_file = request.FILES["csv_file"].read().decode()

        reader = csv.DictReader(StringIO(decoded_file))

        for r in reader:
            imei = r["imei"]

            # get existing modem or start a new model
            try:
                modem = Modem.objects.get(imei=imei)
            except Modem.DoesNotExist:
                modem = Modem(imei=imei)

            # populate fields as available
            if "vsn" in r:
                try:
                    modem.node = NodeData.objects.get(vsn=r["vsn"].upper())
                except NodeData.DoesNotExist:
                    self.message_user(
                        request,
                        f"Node {r['vsn']} does not exist.",
                        level=messages.ERROR,
                    )
            if "imsi" in r:
                modem.imsi = r["imsi"]
            if "iccid" in r:
                modem.iccid = r["iccid"]
            if "carrier" in r:
                modem.carrier = r["carrier"]

            # validate and save model
            try:
                modem.full_clean()
                modem.save()
            except ValidationError as exc:
                self.message_user(
                    request,
                    f"Invalid data for modem {imei}: {exc}",
                    level=messages.ERROR,
                )

        return redirect("..")


@admin.action(description="Add default devices using zone")
def add_default_devices_using_zone(modeladmin, request, queryset):
    nxcore_hw = [
        ComputeHardware.objects.get(hardware="xaviernx"),
    ]
    rpi_hw = [
        ComputeHardware.objects.get(hardware="rpi-4gb"),
        ComputeHardware.objects.get(hardware="rpi-8gb"),
    ]

    bme280 = SensorHardware.objects.get(hardware="bme280")
    bme680 = SensorHardware.objects.get(hardware="bme680")
    gps = SensorHardware.objects.get(hardware="gps")
    raingauge = SensorHardware.objects.get(hardware="raingauge")
    microphone = SensorHardware.objects.get(hardware="microphone")

    for compute in queryset:
        if compute.zone == "core" and compute.hardware in nxcore_hw:
            ComputeSensor.objects.get_or_create(
                scope=compute,
                hardware=bme280,
                name="bme280",
            )
            ComputeSensor.objects.get_or_create(
                scope=compute,
                hardware=gps,
                name="gps",
            )
        elif compute.zone == "shield" and compute.hardware in rpi_hw:
            ComputeSensor.objects.get_or_create(
                scope=compute,
                hardware=bme680,
                name="bme680",
            )
            ComputeSensor.objects.get_or_create(
                scope=compute,
                hardware=raingauge,
                name="raingauge",
            )
            ComputeSensor.objects.get_or_create(
                scope=compute,
                hardware=microphone,
                name="microphone",
            )
        elif compute.zone in ["enclosure", "detector"] and compute.hardware in rpi_hw:
            ComputeSensor.objects.get_or_create(
                scope=compute,
                hardware=bme680,
                name="bme680",
            )


@admin.register(Compute)
class ComputeAdmin(nested_admin.NestedModelAdmin):
    list_display = [
        "name",
        "node",
        "hardware",
        "serial_no",
        "zone",
        "get_sensors",
    ]
    list_filter = ["hardware", "zone"]
    search_fields = [
        "name",
        "node__vsn",
        "hardware__hardware",
        "serial_no",
        "zone",
        "computesensor__name",
    ]
    autocomplete_fields = ["node", "hardware"]
    inlines = [ComputeSensorInline]
    actions = [add_default_devices_using_zone]

    @admin.display(description="Sensors")
    def get_sensors(self, obj):
        return ",".join(
            obj.computesensor_set.values_list("name", flat=True).order_by("name")
        )


@admin.register(LorawanDevice)
class LorawanDeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "deveui", "battery_level"]
    search_fields = ["name", "deveui"]


@admin.register(LorawanConnection)
class LorawanConnectionAdmin(nested_admin.NestedModelAdmin):
    list_display = [
        "connection_name",
        "lorawan_device",
        "node",
        "created_at",
        "last_seen_at",
    ]
    list_filter = ["node", "lorawan_device"]
    search_fields = ["connection_name"]


@admin.register(LorawanKeys)
class LorawanKeysAdmin(admin.ModelAdmin):
    list_display = [
        "lorawan_connection",
        "app_key",
        "network_Key",
        "app_session_key",
        "dev_address",
    ]
    search_fields = ["lorawan_connection"]


admin.site.register(
    ComputeHardware,
    list_display=["hardware", "hw_model", "manufacturer"],
    search_fields=["name"],
)


@admin.register(SensorHardware)
class SensorHardwareAdmin(admin.ModelAdmin):
    list_display = ["hardware", "hw_model", "manufacturer", "is_camera"]
    search_fields = ["hardware", "hw_model", "manufacturer"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("capabilities")

    @admin.display(description="Camera?", boolean=True)
    def is_camera(self, obj):
        return obj.capabilities.filter(capability="camera").exists()


admin.site.register(
    ResourceHardware,
    list_display=["hardware", "hw_model", "manufacturer"],
    search_fields=["name"],
)

admin.site.register(Label)
admin.site.register(Tag)
admin.site.register(Capability)

admin.site.register(NodeBuildProject)
admin.site.register(NodeBuildProjectFocus)
admin.site.register(NodeBuildProjectPartner)


@admin.register(NodeBuild)
class NodeBuildAdmin(admin.ModelAdmin):
    list_display = [
        "vsn",
        "type",
        "project",
        "top_camera",
        "bottom_camera",
        "left_camera",
        "right_camera",
        "agent",
        "shield",
        "extra_rpi",
        "modem",
        "modem_sim_type",
    ]

    list_filter = [
        "type",
        "project",
        "agent",
        "shield",
        "extra_rpi",
        "modem",
        "modem_sim_type",
    ]

    search_fields = [
        "vsn",
        "type",
        "project__name",
        "modem_sim_type",
        "top_camera__hardware",
        "bottom_camera__hardware",
        "left_camera__hardware",
        "right_camera__hardware",
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in [
            "top_camera",
            "bottom_camera",
            "left_camera",
            "right_camera",
        ]:
            kwargs["queryset"] = SensorHardware.objects.filter(
                capabilities__capability="camera",
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(NodeSensor)
class NodeSensorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "hardware",
        "serial_no",
        "uri",
        "node",
    ]
    search_fields = [
        "name",
        "serial_no",
        "uri",
        "hardware__hardware",
        "hardware__hw_model",
        "node__vsn",
    ]
    # We're excluding scope because it seems to be intended to always be set to "default".
    exclude = ["scope"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("hardware", "node")


@admin.register(ComputeSensor)
class ComputeSensorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "hardware",
        "scope",
        "node",
    ]
    search_fields = [
        "name",
        "hardware__hardware",
        "hardware__hw_model",
        "scope__name",
        "scope__node__vsn",
    ]
    # We're exclude scope as currently the scope selectbox just lists the compute name (ex. rpi) but not the vsn,
    # so using it properly is confusing. For now, it's just a convinient way to see all compute sensors and update
    # things like name and serial number.
    exclude = ["scope"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("scope", "scope__node")
