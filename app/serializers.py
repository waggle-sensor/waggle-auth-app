from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Project, Node

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = [
            "url",
            "username",
            "email",
            "name",
            "is_staff",
            "is_superuser",
            "is_approved",
            "ssh_public_keys",
            "date_joined",
            "last_login"
        ]
        extra_kwargs = {
            "url": {"lookup_field": "username", "view_name": "app:user-detail"},
            "users": {"lookup_field": "username"},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        lookup_field = "username"
        fields = ["username", "organization", "department", "bio", "ssh_public_keys"]
        read_only_fields = ["username"]


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ["vsn", "mac"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "name"]


class ProjectSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)
    members = ProjectMemberSerializer(source='users', many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["name", "members", "nodes"]

