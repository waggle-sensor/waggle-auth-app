from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse
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
class NodeMetaData(nested_admin.NestedModelAdmin):
    actions = [export_as_json]

    # display in admin panel
    list_display = (
        "vsn",
        "name",
        "gps_lat",
        "gps_lon",
        "get_tags",
        "get_computes",
    )
    search_fields = ("vsn", "name")
    ordering = ("vsn",)

    fieldsets = (
        (None, {"fields": ("vsn", "name", "tags")}),
        ("Location", {"fields": ("gps_lat", "gps_lon")}),
    )

    @admin.display(description="Tags")
    def get_tags(self, obj):
        return ", ".join([t.tag for t in obj.tags.all()])

    @admin.display(description="Computes")
    def get_computes(self, obj):
        return ", ".join([c.hardware for c in obj.computes.all()])

    inlines = [ModemInline, ComputeInline, NodeSensorInline, ResourceInline]


admin.site.register(
    Modem,
    list_display=["imei", "imsi", "iccid", "node", "sim_type", "model"],
    search_fields=["imei", "imsi", "iccid", "node__vsn", "sim_type"],
)
admin.site.register(Label)
admin.site.register(Tag)
admin.site.register(
    ComputeHardware, list_display=["hardware", "hw_model", "manufacturer"]
)
admin.site.register(
    SensorHardware, list_display=["hardware", "hw_model", "manufacturer"]
)
admin.site.register(
    ResourceHardware, list_display=["hardware", "hw_model", "manufacturer"]
)
admin.site.register(Capability)
