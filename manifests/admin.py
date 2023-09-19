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


# admin page actions
@admin.action(description="Export as JSON")
def export_as_json(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    serializers.serialize(
        "json", queryset, stream=response, use_natural_foreign_keys=True
    )
    return response


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
    actions = [export_as_json]

    # display in admin panel
    list_display = (
        "vsn",
        "name",
        "phase",
        "address",
        "gps_lat",
        "gps_lon",
        "get_computes",
        "registered_at",
    )
    list_filter = ("phase", "registered_at")
    search_fields = ("vsn", "name", "phase", "notes", "address", "compute__name")
    ordering = ("vsn",)

    fieldsets = (
        (None, {"fields": ("vsn", "name", "phase", "notes", "tags", "registered_at")}),
        ("Location", {"fields": ("address", "gps_lat", "gps_lon")}),
    )

    @admin.display(description="Tags")
    def get_tags(self, obj):
        return ",".join(obj.tags.values_list("tag", flat=True).order_by("tag"))

    @admin.display(description="Computes")
    def get_computes(self, obj):
        return ",".join(obj.compute_set.values_list("name", flat=True).order_by("name"))

    inlines = [ModemInline, ComputeInline, NodeSensorInline, ResourceInline]


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

    @admin.display(description="Sensors")
    def get_sensors(self, obj):
        return ",".join(
            obj.computesensor_set.values_list("name", flat=True).order_by("name")
        )


admin.site.register(
    ComputeHardware,
    list_display=["hardware", "hw_model", "manufacturer"],
    search_fields=["name"],
)
admin.site.register(
    SensorHardware,
    list_display=["hardware", "hw_model", "manufacturer"],
    search_fields=["name"],
)
admin.site.register(
    ResourceHardware,
    list_display=["hardware", "hw_model", "manufacturer"],
    search_fields=["name"],
)

admin.site.register(Label)
admin.site.register(Tag)
admin.site.register(Capability)
