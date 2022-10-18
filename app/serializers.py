from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "name", "is_staff", "is_superuser", "ssh_public_keys"]
        extra_kwargs = {
            "url": {"lookup_field": "username", "view_name": "app:user-detail"},
            "users": {"lookup_field": "username"},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        lookup_field = 'username'
        fields = ["username", "organization", "department", "bio"]
        read_only_fields = ["username"]
