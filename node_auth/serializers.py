from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from app.models import Node
from node_auth.models import Token
from django.conf import settings

class AuthTokenSerializer(serializers.Serializer):
    vsn = serializers.CharField()

    def validate(self, attrs):
        vsn = attrs.get("vsn")

        if Node.objects.filter(vsn=vsn).exists():
            node = Node.objects.get(vsn=vsn)
        else:
            msg = _("Node not registered")
            raise serializers.ValidationError(msg)

        attrs["vsn"] = node
        return attrs

class WireGuardSerializer(serializers.ModelSerializer):
    node_wg_pub_key = serializers.CharField(source="wg_pub_key", read_only=True)
    node_wg_priv_key = serializers.CharField(source="wg_priv_key", read_only=True)
    node_wg_ip = serializers.CharField(source="node.vpn_ip", read_only=True)

    server_pub_key = serializers.SerializerMethodField()
    server_pub_ip = serializers.SerializerMethodField()
    server_wg_port = serializers.SerializerMethodField()
    server_wg_ip = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = [
            "node_wg_pub_key",
            "node_wg_priv_key",
            "node_wg_ip",
            "server_pub_key",
            "server_pub_ip",
            "server_wg_port",
            "server_wg_ip"
        ]

    def get_server_pub_key(self, obj):
        return settings.WG_PUB_KEY

    def get_server_pub_ip(self, obj):
        return settings.WG_PUBLIC_IP

    def get_server_wg_port(self, obj):
        return settings.WG_PORT

    def get_server_wg_ip(self, obj):
        return settings.WG_SERVER_ADDRESS