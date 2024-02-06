"""
Used django.contrib.auth.base_user as a Template
"""
import unicodedata
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class AbstractBaseNode(models.Model):

    is_active = True
    REQUIRED_FIELDS = ["vsn"]

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_vsn()

    def get_vsn(self):
        """Return the vsn for this Node."""
        return getattr(self, self.VSN_FIELD)

    def natural_key(self):
        return (self.get_vsn(),) 