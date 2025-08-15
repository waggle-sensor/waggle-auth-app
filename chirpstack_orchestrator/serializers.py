"""
Marshals HTTP request payloads → validated Python primitives for the
Chirpstack ViewSets.  These serializers **do not** perform any database I/O;
they only enforce schema and basic field-level validation before we pass the
data to chirpstack_api_wrapper objects (which handle the gRPC side).
"""
from rest_framework import serializers
from chirpstack_api_wrapper.objects import (
    Region,
    MacVersion,
    RegParamsRevision,
    CodecRuntime,
    AdrAlgorithm,
    ClassBPingSlot,
)

class EnumChoiceField(serializers.ChoiceField):
    """
    Accepts either the **name** (e.g. "EU868") or the **value** (e.g. 0)
    of an Enum member and stores the Enum *member* itself.
    """

    def __init__(self, enum_class, **kwargs):
        self.enum_class = enum_class
        # Build DRF choices mapping for browsable API
        choices = {e.name: e.name for e in enum_class}
        super().__init__(choices=choices, **kwargs)

    def to_internal_value(self, data):
        # Allow value (int / str) or name (str) or Enum member
        if isinstance(data, self.enum_class):
            return data
        try:
            return self.enum_class[data]           # by name
        except (KeyError, TypeError):
            # by value
            for member in self.enum_class:
                if str(member.value) == str(data):
                    return member
        self.fail("invalid_choice", input=data)

    def to_representation(self, value):
        return value.name if isinstance(value, self.enum_class) else str(value)

class TagField(serializers.DictField):
    """
    A field for storing tags or variables as a dictionary.
    Allows empty dictionaries and does not require any specific keys.
    """
    child = serializers.CharField()

class ApplicationSerializer(serializers.Serializer):
    """Serializer for Application objects."""
    name        = serializers.CharField(max_length=100)
    tenant_id   = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    tags        = TagField(required=False, default=dict)

class DeviceSerializer(serializers.Serializer):
    """Serializer for Device objects."""
    name              = serializers.CharField(max_length=100)
    dev_eui           = serializers.CharField(max_length=16)
    application_id    = serializers.CharField()
    device_profile_id = serializers.CharField()
    join_eui          = serializers.CharField(max_length=16, required=False, allow_blank=True)
    description       = serializers.CharField(required=False, allow_blank=True)
    skip_fcnt_check   = serializers.BooleanField(default=False)
    is_disabled       = serializers.BooleanField(default=False)
    tags              = TagField(required=False, default=dict)
    variables         = TagField(required=False, default=dict)

    def validate_dev_eui(self, value):
        if len(value) != 16:
            raise serializers.ValidationError("dev_eui must be 16-char hex EUI-64.")
        return value.lower()

    def validate_join_eui(self, value):
        if value and len(value) != 16:
            raise serializers.ValidationError("join_eui must be 16-char hex EUI-64.")
        return value.lower()

class GatewaySerializer(serializers.Serializer):
    """Serializer for Gateway objects."""
    gateway_id    = serializers.CharField(max_length=16)
    name          = serializers.CharField(max_length=100)
    tenant_id     = serializers.CharField()
    description   = serializers.CharField(required=False, allow_blank=True)
    stats_interval = serializers.IntegerField(required=False, min_value=1, default=30)
    tags          = TagField(required=False, default=dict)

    def validate_gateway_id(self, value):
        if len(value) != 16:
            raise serializers.ValidationError("gateway_id must be 16-char hex EUI-64.")
        return value.lower()

class DeviceProfileSerializer(serializers.Serializer):
    """Serializer for DeviceProfile objects."""
    # core
    name                = serializers.CharField(max_length=100)
    tenant_id           = serializers.CharField()
    region              = EnumChoiceField(Region)
    mac_version         = EnumChoiceField(MacVersion)
    reg_params_revision = EnumChoiceField(RegParamsRevision)
    uplink_interval     = serializers.IntegerField(min_value=1)
    supports_otaa       = serializers.BooleanField()
    supports_class_b    = serializers.BooleanField()
    supports_class_c    = serializers.BooleanField()
    description         = serializers.CharField(required=False, allow_blank=True)

    # codec
    payload_codec_runtime = EnumChoiceField(CodecRuntime, required=False, default=CodecRuntime.NONE)
    payload_codec_script  = serializers.CharField(required=False, allow_blank=True)

    # flags
    flush_queue_on_activate    = serializers.BooleanField(default=True)
    device_status_req_interval = serializers.IntegerField(required=False, min_value=0, default=1)
    auto_detect_measurements   = serializers.BooleanField(default=True)
    allow_roaming              = serializers.BooleanField(default=False)
    adr_algorithm_id           = EnumChoiceField(AdrAlgorithm, required=False, default=AdrAlgorithm.LORA_ONLY)
    tags                       = TagField(required=False, default=dict)

    # ABP (when OTAA disabled)
    abp_rx1_delay     = serializers.IntegerField(required=False)
    abp_rx1_dr_offset = serializers.IntegerField(required=False)
    abp_rx2_dr        = serializers.IntegerField(required=False)
    abp_rx2_freq      = serializers.IntegerField(required=False)

    # Class-B extras
    class_b_timeout        = serializers.IntegerField(required=False)
    class_b_ping_slot_nb_k = EnumChoiceField(ClassBPingSlot, required=False, default=ClassBPingSlot.NONE)
    class_b_ping_slot_dr   = serializers.IntegerField(required=False)
    class_b_ping_slot_freq = serializers.IntegerField(required=False)

    # Class-C
    class_c_timeout = serializers.IntegerField(required=False)

    # --- conditional validation ------------------------------------------

    def validate(self, data):
        # ABP parameters required if OTAA disabled
        if not data["supports_otaa"]:
            missing = [f for f in ("abp_rx1_delay", "abp_rx1_dr_offset", "abp_rx2_dr", "abp_rx2_freq") if data.get(f) is None]
            if missing:
                raise serializers.ValidationError(
                    f"ABP devices require fields: {', '.join(missing)}"
                )

        # Class-B params
        if data["supports_class_b"]:
            required_b = [f for f in ("class_b_timeout", "class_b_ping_slot_dr", "class_b_ping_slot_freq") if data.get(f) is None]
            if required_b:
                raise serializers.ValidationError(
                    f"Class-B devices require fields: {', '.join(required_b)}"
                )

        # Class-C params
        if data["supports_class_c"] and data.get("class_c_timeout") is None:
            raise serializers.ValidationError("class_c_timeout is required when supports_class_c is true")

        return data
