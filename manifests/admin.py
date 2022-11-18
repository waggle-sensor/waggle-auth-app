from dataclasses import fields
from django.contrib import admin
from .models import *
from django.core import serializers
from django.http import HttpResponse
from nested_inline.admin import NestedStackedInline, NestedModelAdmin

# admin page actions
@admin.action(description='Export as JSON')
def export_as_json(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    serializers.serialize("json", queryset, stream=response, use_natural_foreign_keys=True)
    return response

# Register your models here.
class ResourceInline(NestedStackedInline):
    model = Resource
    fk_name = 'node'

class ComputeSensorInline(NestedStackedInline):
    model = ComputeSensor
    extra = 1
    fk_name = 'scope'

class ComputeInline(NestedStackedInline):
    model = Compute
    extra = 1
    fk_name = 'node'
    inlines = [ComputeSensorInline]

class NodeSensorInline(NestedStackedInline):
    model = NodeSensor
    fk_name = 'node'

class NodeMetaData(NestedModelAdmin):
    actions = [export_as_json]

    # display in admin panel
    list_display = ('VSN', 'name','gps_lat', 'gps_lan', 'get_tags', 'get_computes')

    @admin.display(description='Tags')
    def get_tags(self, obj):
        return ", ".join([t.tag for t in obj.tags.all()])

    @admin.display(description='Computes')
    def get_computes(self, obj):
        return ", ".join([c.hardware for c in obj.computes.all()])

    inlines = [
        ComputeInline,
        NodeSensorInline,
        ResourceInline
    ]


admin.site.register(NodeData, NodeMetaData)
admin.site.register(Label)
admin.site.register(Tag)
admin.site.register(Hardware)
admin.site.register(Capability)
