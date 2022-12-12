from .models import *
from collections import defaultdict
from rest_framework import serializers

# TODO(sean) try to improve this by naming relationships more conviniently in models.py, especially for many-to-many stuff.

class NodeComputeHardwareSerializer(serializers.ModelSerializer):
    capabilities = serializers.StringRelatedField(many=True)

    class Meta:
        model = ComputeHardware
        exclude = ["id"]


class NodeComputeSerializer(serializers.ModelSerializer):
    hardware = NodeComputeHardwareSerializer()

    class Meta:
        model = Compute
        exclude = ["id", "node"]


class NodeSensorHardwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorHardware
        exclude = ["id"]


class NodeSensorSerializer(serializers.ModelSerializer):
    hardware = NodeSensorHardwareSerializer()

    class Meta:
        model = NodeSensor
        exclude = ["id", "node"]


class NodeResourceHardwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceHardware
        exclude = ["id"]


class NodeResourceSerializer(serializers.ModelSerializer):
    hardware = NodeResourceHardwareSerializer()

    class Meta:
        model = Resource
        exclude = ["id", "node"]


class NodeSerializer(serializers.ModelSerializer):
    computes = NodeComputeSerializer(many=True, source="compute_set")
    sensors = NodeSensorSerializer(many=True, source="nodesensor_set")
    resources = NodeResourceSerializer(many=True, source="resource_set")
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = NodeData
        exclude = ["id"]
