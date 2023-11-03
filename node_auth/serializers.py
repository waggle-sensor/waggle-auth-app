from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from app.models import Node


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
