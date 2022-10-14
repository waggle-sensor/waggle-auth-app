from django.conf import settings
from django.db import models


class Identity(models.Model):
    sub = models.UUIDField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="oidc_identity", on_delete=models.SET_NULL, null=True)
    preferred_username = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    organization = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Identities"
