from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = User
        fields = ["url", "username", "email", "name", "groups"]
        extra_kwargs = {
            "url": {"lookup_field": "username", "view_name": "app:user-detail"},
            "users": {"lookup_field": "username"},
        }
