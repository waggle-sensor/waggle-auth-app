from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from app.models import Node
from .models import Token


class AuthTokenSerializer(serializers.ModelSerializer):
    node = serializers.CharField(source="node.vsn")

    class Meta:
        model = Token
        fields = "__all__"

    def validate(self, attrs):
        vsn = attrs.get("node")['vsn']

        if Node.objects.filter(vsn=vsn).exists():
            node = Node.objects.get(vsn=vsn)
        else:
            msg = _("Node not registered")
            raise serializers.ValidationError(msg)

        return attrs