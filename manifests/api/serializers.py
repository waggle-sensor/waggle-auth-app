from ..models import *
from collections import defaultdict
from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer


class NodeSerializer(WritableNestedModelSerializer):
    computes = serializers.SerializerMethodField("get_computes")
    resources = serializers.SerializerMethodField("get_resources")
    tags = serializers.StringRelatedField(many=True)
    sensors = serializers.SerializerMethodField("get_sensors")

    def get_computes(self, obj):
        node = obj.id
        compute = []
        compute_obj = []
        compute_obj.extend(c for c in Compute.objects.filter(node__id=node))

        for c in compute_obj:
            compute_dict = defaultdict()
            compute_dict["hardware"] = defaultdict(list)
            h = Hardware.objects.get(hardware=c.hardware)
            cap_obj = h.capabilities.all()

            compute_dict["name"] = c.name
            compute_dict["serial_no"] = c.serial_no
            compute_dict["zone"] = c.zone
            compute_dict["hardware"]["hardware"] = h.hardware
            compute_dict["hardware"]["hw_model"] = h.hw_model
            compute_dict["hardware"]["hw_version"] = h.hw_version
            compute_dict["hardware"]["sw_version"] = h.sw_version
            compute_dict["hardware"]["datasheet"] = h.datasheet
            compute_dict["hardware"]["cpu"] = h.cpu
            compute_dict["hardware"]["cpu_ram"] = h.cpu_ram
            compute_dict["hardware"]["gpu_ram"] = h.gpu_ram
            compute_dict["hardware"]["shared_ram"] = h.shared_ram
            compute_dict["hardware"]["capabilities"] = [cap.capability for cap in cap_obj]

            compute.append(compute_dict)

        return compute

    def get_sensors(self, obj):
        node = obj.id
        compute_id = []
        sensor_obj = []
        sensor = []

        # collect sensors from NodeSensor & ComputeSensor(needs to collect Computes first)
        compute_id.extend(c.id for c in Compute.objects.filter(node__id=node))
        sensor_obj.extend(s for s in NodeSensor.objects.filter(node__id=node))

        for c in compute_id:
            sensor_obj.extend(s for s in ComputeSensor.objects.filter(scope__id=c))

        for s_o in sensor_obj:
            sensor_dict = defaultdict()
            sensor_dict["hardware"] = defaultdict(list)
            h = Hardware.objects.get(hardware=s_o.hardware)
            cap_obj = h.capabilities.all()
            lab_obj = s_o.labels.all()

            sensor_dict["name"] = s_o.name
            sensor_dict["scope"] = str(s_o.scope)
            sensor_dict["labels"] = [l.label for l in lab_obj]
            sensor_dict["hardware"]["hardware"] = h.hardware
            sensor_dict["hardware"]["hw_model"] = h.hw_model
            sensor_dict["hardware"]["hw_version"] = h.hw_version
            sensor_dict["hardware"]["sw_version"] = h.sw_version
            sensor_dict["hardware"]["datasheet"] = h.datasheet
            sensor_dict["hardware"]["cpu"] = h.cpu
            sensor_dict["hardware"]["cpu_ram"] = h.cpu_ram
            sensor_dict["hardware"]["gpu_ram"] = h.gpu_ram
            sensor_dict["hardware"]["shared_ram"] = h.shared_ram
            sensor_dict["hardware"]["capabilities"] = [cap.capability for cap in cap_obj]

            sensor.append(sensor_dict)

        return sensor

    def get_resources(self, obj):
        node = obj.id
        resource = []
        resource_obj = []

        resource_obj.extend(r for r in Resource.objects.filter(node__id=node))

        for r in resource_obj:
            resource_dict = defaultdict()
            resource_dict["hardware"] = defaultdict(list)
            h = Hardware.objects.get(hardware=r.hardware)
            cap_obj = h.capabilities.all()

            resource_dict["name"] = r.name
            resource_dict["hardware"]["hardware"] = h.hardware
            resource_dict["hardware"]["hw_model"] = h.hw_model
            resource_dict["hardware"]["hw_version"] = h.hw_version
            resource_dict["hardware"]["sw_version"] = h.sw_version
            resource_dict["hardware"]["datasheet"] = h.datasheet
            resource_dict["hardware"]["cpu"] = h.cpu
            resource_dict["hardware"]["cpu_ram"] = h.cpu_ram
            resource_dict["hardware"]["gpu_ram"] = h.gpu_ram
            resource_dict["hardware"]["shared_ram"] = h.shared_ram
            resource_dict["hardware"]["capabilities"] = [cap.capability for cap in cap_obj]

            resource.append(resource_dict)

        return resource

    class Meta:
        model = NodeData
        fields = ('VSN', 'name', 'tags', 'computes', 'sensors', 'resources', )