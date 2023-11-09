from rest_framework import serializers
from .models import *


class SensorHardwareSerializer(serializers.ModelSerializer):
    # replace capabilities IDs by their names
    capabilities = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="capability", required=False
    )

    class Meta:
        model = SensorHardware
        # to preserve the fields order, we'll list them explicitly
        fields = [
            "hardware",
            "hw_model",
            "hw_version",
            "sw_version",
            "manufacturer",
            "datasheet",
            "description",
            "capabilities",
        ]


class ModemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modem
        fields = ["model", "sim_type", "carrier"]


class LorawanDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LorawanDevice
        fields = "__all__"


class LorawanConnectionSerializer(serializers.ModelSerializer):
    node = serializers.CharField(
        source="node.vsn"
    )  # Use the 'vsn' field as the source for node field
    lorawan_device = serializers.CharField(
        source="lorawan_device.deveui"
    )  # Use the 'deveui' field as the source for lorawan device field

    class Meta:
        model = LorawanConnection
        fields = "__all__"


class ManifestSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source="project.name", allow_null=True)
    modem = ModemSerializer()
    computes = serializers.SerializerMethodField("get_computes")
    resources = serializers.SerializerMethodField("get_resources")
    tags = serializers.StringRelatedField(many=True)
    sensors = serializers.SerializerMethodField("get_sensors")
    lorawanconnections = serializers.SerializerMethodField("get_lorawan_connections")

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

    def get_lorawan_connections(self, obj: NodeData):
        return [serialize_lorawan_connections(l) for l in obj.lorawanconnections.all()]

    class Meta:
        model = NodeData
        fields = (
            "vsn",
            "name",
            "phase",
            "project",
            "address",
            "gps_lat",
            "gps_lon",
            "modem",
            "tags",
            "computes",
            "sensors",
            "resources",
            "lorawanconnections",
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


def serialize_lorawan_devices(l):
    return {
        "deveui": l.deveui,
        "device_name": l.device_name,
        "battery_level": l.battery_level,
    }


def serialize_lorawan_connections(l):
    return {
        "connection_name": l.connection_name,
        "created_at": l.created_at,
        "last_seen_at": l.last_seen_at,
        "margin": l.margin,
        "expected_uplink_interval_sec": l.expected_uplink_interval_sec,
        "lorawandevice": serialize_lorawan_devices(l.lorawan_device),
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


class NodesSerializer(serializers.ModelSerializer):
    computes = serializers.SerializerMethodField("get_computes")
    sensors = serializers.SerializerMethodField("get_sensors")

    class Meta:
        model = NodeData
        fields = ['address', 'gps_lat', 'gps_lon', 'registered_at', 'sensors', 'computes']

    def serialize_compute(self, c):
        return {
            "name": c.name,
            "serial_no": c.serial_no,
            "zone": c.zone,
        }

    def get_computes(self, obj: NodeData):
        return [self.serialize_compute(c) for c in obj.compute_set.all()]

    def get_sensors(self, obj: NodeData):
        results = []

        # add all node sensors
        for s in obj.nodesensor_set.all():
            results.append(self.serialize_common_sensor(s))

        return results

    def serialize_common_sensor(self, s):
        return {
            "name": s.name,
            "labels": [l.label for l in s.labels.all()],
        }