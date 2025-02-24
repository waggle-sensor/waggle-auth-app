from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from .models import *


class SensorViewSerializer(serializers.ModelSerializer):
    # replace capabilities IDs by their names
    capabilities = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="capability", required=False
    )
    vsns = serializers.SerializerMethodField()

    def get_vsns(self, obj):
        compute_sensors = obj.computesensor_set.all()
        node_sensors = obj.nodesensor_set.all()
        lorawan_sensors = obj.lorawandevice_set.all()
        lorawan_connections = [ld.lorawanconnections.filter(is_active=True) for ld in lorawan_sensors]
        nodes = (
            [s.scope.node for s in compute_sensors]
            + [s.node for s in node_sensors]
            + [lc[0].node for lc in lorawan_connections if lc]
        )

        project = self.context["request"].query_params.get("project")
        if project:
            projects = project.split(",")
            nodes = [
                node
                for node in nodes
                if node.project
                and node.project.name.lower() in (p.lower() for p in projects)
            ]

        phase = self.context["request"].query_params.get("phase")
        if phase:
            phases = phase.split(",")
            nodes = [
                node
                for node in nodes
                if node.phase
                and node.phase.lower() in (p.lower() for p in phases)
            ]

        vsns = sorted(set([node.vsn for node in nodes]))

        return vsns

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
            "vsns",
        ]


class SensorHardwareCRUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorHardware
        fields = "__all__"


class ModemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modem
        fields = ["model", "sim_type", "carrier"]


class LorawanDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LorawanDevice
        fields = "__all__"


class LorawanConnectionSerializer(serializers.ModelSerializer):
    node = (
        serializers.CharField()
    )  # turn into char field to get rid of error ""Incorrect type. Expected pk value, received str.""

    class Meta:
        model = LorawanConnection
        fields = "__all__"

    def get_node(self, vsn):
        """Validate and retrieve the NodeData instance"""
        try:
            node = NodeData.objects.get(vsn=vsn)
        except NodeData.DoesNotExist:
            raise serializers.ValidationError(
                {"node": [f'Invalid vsn "{vsn}" - object does not exist.']}
            )
        return node

    def get_lookup_records(self, validated_data):
        """Retrieve lookup field record based on custom logic"""
        node_data = validated_data.pop("node", None)

        if node_data:
            validated_data["node"] = self.get_node(node_data)

        return validated_data

    def create(self, validated_data):
        """
        Retrieve lookup field records based on validated data
        to then pass in to parent create function
        """
        validated_data = self.get_lookup_records(validated_data)
        # this has to be added because serializer is checking for node pk and lorawan device pk so it passes since im using node vsn NOT pk
        #  serializer thinks a lc has not been created with this combination of node and lorawan device and causes a server error - FL 01/26/24
        if LorawanConnection.objects.filter(
            node=validated_data["node"], lorawan_device=validated_data["lorawan_device"]
        ).exists():
            raise serializers.ValidationError(
                {
                    "node-lorawan_device": [
                        f"Lorawan connection with this node and lorawan_device already exists"
                    ]
                }
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Retrieve lookup field records based on validated data
        to then pass in to parent update function
        """
        return super().update(instance, self.get_lookup_records(validated_data))


class LorawanKeysSerializer(serializers.ModelSerializer):
    lorawan_connection = serializers.CharField()

    class Meta:
        model = LorawanKeys
        fields = "__all__"

    def validate_lorawan_connection(self, value):
        """Ensure that lorawan_connection is in the format "node-device_name-deveui"""
        try:
            node_vsn, device_name, deveui = value.split("-")
        except ValueError:
            raise serializers.ValidationError(
                "Invalid lorawan_connection format. Use 'node-device_name-deveui'."
            )
        return value

    def get_lc(self, lc_str):
        """Validate and retrieve the lorawan connection instance"""
        try:
            node_vsn, lorawan_device_name, lorawan_device_deveui = lc_str.split("-")
            lc = LorawanConnection.objects.get(
                node__vsn=node_vsn,
                lorawan_device__name=lorawan_device_name,
                lorawan_device__deveui=lorawan_device_deveui,
            )
        except LorawanConnection.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "lorawan_connection": [
                        f'Invalid connection "{lc_str}" - object does not exist.'
                    ]
                }
            )
        return lc

    def get_lookup_records(self, validated_data):
        """Retrieve lookup field record based on custom logic"""
        lc = validated_data.pop("lorawan_connection", None)

        if lc:
            validated_data["lorawan_connection"] = self.get_lc(lc)

        return validated_data

    def create(self, validated_data):
        """
        Retrieve lookup field records based on validated data
        to then pass in to parent create function
        """
        # same issue here as lorawan connection serializer - FL
        validated_data = self.get_lookup_records(validated_data)
        if LorawanKeys.objects.filter(
            lorawan_connection=validated_data["lorawan_connection"]
        ).exists():
            raise serializers.ValidationError(
                {
                    "lorawan_connection": [
                        f"Lorawan Key with this lorawan_connection already exists"
                    ]
                }
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Retrieve lookup field records based on validated data
        to then pass in to parent update function
        """
        return super().update(instance, self.get_lookup_records(validated_data))


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
        return [serialize_lorawan_connections(l) for l in obj.lorawanconnections.filter(is_active=True)]

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
        "is_active": c.is_active,
        "serial_no": c.serial_no,
        "zone": c.zone,
        "hardware": serialize_compute_hardware(c.hardware),
    }


def serialize_common_sensor(s):
    return {
        "name": s.name,
        "is_active": s.is_active,
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
        "name": l.name,
        "is_active": l.is_active,
        "battery_level": l.battery_level,
        "hardware": serialize_common_hardware(l.hardware),
    }


def serialize_lorawan_connections(l):
    return {
        "connection_name": l.connection_name,
        "created_at": l.created_at,
        "last_seen_at": l.last_seen_at,
        "margin": l.margin,
        "expected_uplink_interval_sec": l.expected_uplink_interval_sec,
        "connection_type": l.connection_type,
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
    focus = serializers.CharField(source="focus.name", allow_null=True)
    partner = serializers.CharField(source="partner.name", allow_null=True)
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
            "focus",
            "partner",
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
    modem_model = serializers.SerializerMethodField("get_modem_model")
    modem_sim = serializers.CharField(source="modem.sim_type", read_only=True)
    modem_carrier = serializers.CharField(source="modem.carrier", read_only=True)
    project = serializers.CharField(source="project.name", read_only=True)
    focus = serializers.CharField(source="focus.name", read_only=True)
    partner = serializers.CharField(source="partner.name", read_only=True)
    addr_formatted = serializers.CharField(source="address.formatted", read_only=True)
    streetnum = serializers.CharField(source="address.street_number", read_only=True)
    route = serializers.CharField(source="address.route", read_only=True)
    town = serializers.CharField(source="address.locality.name", read_only=True)
    postal_code = serializers.CharField(
        source="address.locality.postal_code", read_only=True
    )
    state = serializers.CharField(source="address.locality.state.name", read_only=True)
    state_code = serializers.CharField(
        source="address.locality.state.code", read_only=True
    )
    country = serializers.CharField(
        source="address.locality.state.country.name", read_only=True
    )
    country_code = serializers.CharField(
        source="address.locality.state.country.code", read_only=True
    )

    class Meta:
        model = NodeData
        fields = [
            "id",
            "vsn",
            "name",
            "project",
            "focus",
            "partner",
            "type",
            "site_id",
            "gps_lat",
            "gps_lon",
            "gps_alt",
            "address",
            "addr_formatted",
            "streetnum",
            "route",
            "town",
            "state",
            "state_code",
            "postal_code",
            "country",
            "country_code",
            "location",
            "phase",
            "commissioned_at",
            "registered_at",
            "modem_sim",
            "modem_model",
            "modem_carrier",
            "sensors",
            "computes",
        ]

    @staticmethod
    def serialize_compute(c):
        return {
            "name": c.name,
            "is_active": c.is_active,
            "serial_no": c.serial_no,
            "hw_model": c.hardware.hw_model,
            "manufacturer": c.hardware.manufacturer,
            "capabilities": [cap.capability for cap in c.hardware.capabilities.all()],
        }

    @staticmethod
    def serialize_common_sensor(s):
        return {
            "name": s.name,
            "is_active": s.is_active,
            "hw_model": s.hardware.hw_model,
            "manufacturer": s.hardware.manufacturer,
            "capabilities": [cap.capability for cap in s.hardware.capabilities.all()],
        }

    def get_computes(self, obj: NodeData):
        return [self.serialize_compute(c) for c in obj.compute_set.all()]

    def get_sensors(self, obj: NodeData):
        results = []

        # add all node sensors
        for s in obj.nodesensor_set.all():
            results.append(self.serialize_common_sensor(s))

        # add all compute sensors
        for c in obj.compute_set.all():
            for s in c.computesensor_set.all():
                results.append(self.serialize_common_sensor(s))

        # add all lorawan sensors
        for s in obj.lorawanconnections.filter(is_active=True):
            results.append(self.serialize_common_sensor(s.lorawan_device))

        return results

    def get_modem_model(self, obj):
        return obj.modem.get_model_display() if hasattr(obj, "modem") else None
