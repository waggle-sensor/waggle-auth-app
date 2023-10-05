from rest_framework import serializers
from .models import *


class SensorHardwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorHardware
        exclude = ["id"]


class ModemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modem
        fields = ["model", "sim_type", "carrier"]


class ManifestSerializer(serializers.ModelSerializer):
    modem = ModemSerializer()
    computes = serializers.SerializerMethodField("get_computes")
    resources = serializers.SerializerMethodField("get_resources")
    tags = serializers.StringRelatedField(many=True)
    sensors = serializers.SerializerMethodField("get_sensors")

    def get_computes(self, obj: NodeData):
        return [serialize_compute(c) for c in obj.compute_set.all()]

    def get_sensors(self, obj: NodeData):
        results = []

        # add all node sensors
        for s in obj.nodesensor_set.all():
            results.append(serialize_common_sensor(s))

        # add all compute sensors
        for c in obj.compute_set.all():
            for s in c.computesensor_set.all():
                results.append(serialize_common_sensor(s))

        return results

    def get_resources(self, obj: NodeData):
        return [serialize_resource(r) for r in obj.resource_set.all()]

    class Meta:
        model = NodeData
        fields = (
            "vsn",
            "name",
            "phase",
            "address",
            "gps_lat",
            "gps_lon",
            "modem",
            "tags",
            "computes",
            "sensors",
            "resources",
        )


def serialize_compute(c):
    return {
        "name": c.name,
        "serial_no": c.serial_no,
        "zone": c.zone,
        "hardware": serialize_compute_hardware(c.hardware),
    }


def serialize_common_sensor(s):
    return {
        "name": s.name,
        "scope": str(s.scope),
        "labels": [l.label for l in s.labels.all()],
        "serial_no": s.serial_no,
        "uri": s.uri,
        "hardware": serialize_common_hardware(s.hardware),
    }


def serialize_resource(r):
    return {
        "name": r.name,
        "hardware": serialize_common_hardware(r.hardware),
    }


def serialize_common_hardware(h):
    return {
        "hardware": h.hardware,
        "hw_model": h.hw_model,
        "hw_version": h.hw_version,
        "sw_version": h.sw_version,
        "manufacturer": h.manufacturer,
        "datasheet": h.datasheet,
        "capabilities": [cap.capability for cap in h.capabilities.all()],
        "description": h.description,
    }


def serialize_compute_hardware(h):
    return {
        **serialize_common_hardware(h),
        "cpu": h.cpu,
        "cpu_ram": h.cpu_ram,
        "gpu_ram": h.gpu_ram,
        "shared_ram": h.shared_ram,
    }


class ComputeSerializer(serializers.ModelSerializer):
    node = serializers.CharField(source="node.vsn")
    hardware = serializers.CharField(source="hardware.hardware")

    class Meta:
        model = Compute
        fields = [
            "node",
            "hardware",
            "name",
            "serial_no",
            "zone",
        ]


class NodeBuildSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source="project.name", allow_null=True)
    top_camera = serializers.CharField(source="top_camera.hardware", allow_null=True)
    bottom_camera = serializers.CharField(
        source="bottom_camera.hardware", allow_null=True
    )
    left_camera = serializers.CharField(source="left_camera.hardware", allow_null=True)
    right_camera = serializers.CharField(
        source="right_camera.hardware", allow_null=True
    )

    class Meta:
        model = NodeBuild
        fields = [
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
        
class LoRaWANDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoRaWANDevice
        fields = '__all__'
