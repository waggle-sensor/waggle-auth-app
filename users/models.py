from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    # Use name instead of assuming cultural convention first and last name.
    name = models.CharField(blank=True, max_length=255)
    first_name = None
    last_name = None
    organization = models.CharField(blank=True, max_length=255)
    bio = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})
