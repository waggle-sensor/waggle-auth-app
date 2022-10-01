from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "is_superuser", "is_staff", "is_active"]
        extra_kwargs = {
            "url": {"lookup_field": "username"},
            "users": {"lookup_field": "username"},
        }
