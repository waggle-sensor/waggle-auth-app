from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import re

ssh_public_key_re = re.compile("^ssh-(\S+) (\S+)")


def validate_ssh_public_key_list(value: str):
    lines = value.splitlines()
    if len(lines) > 5:
        raise ValidationError(f"You may only have up to five keys.", params={"value": value})
    for line in lines:
        if not ssh_public_key_re.match(line):
            raise ValidationError(f"Enter a valid list of newline delimited SSH public keys.", params={"value": value})


class User(AbstractUser):
    # Use name instead of assuming cultural convention first and last name.
    name = models.CharField(blank=True, max_length=255)
    first_name = None
    last_name = None
    organization = models.CharField(blank=True, max_length=255)
    bio = models.TextField(blank=True)
    ssh_public_keys = models.TextField("SSH public keys", blank=True,
        validators=[validate_ssh_public_key_list])

    def get_absolute_url(self):
        return reverse("app:user-detail", kwargs={"username": self.username})


class Node(models.Model):
    vsn = models.CharField("VSN", max_length=10, unique=True)
    mac = models.CharField("MAC", max_length=16, unique=True, null=True, blank=True)

    def __str__(self):
        return self.vsn


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(User, through="UserMembership")
    nodes = models.ManyToManyField(Node, through="NodeMembership")

    def __str__(self):
        return self.name

    def number_of_users(self):
        return self.users.count()

    def number_of_nodes(self):
        return self.nodes.count()


class UserMembership(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_schedule = models.BooleanField(
        "Schedule?",
        default=False,
        help_text="Designates whether user can schedule."
    )
    can_develop = models.BooleanField(
        "Develop?",
        default=False,
        help_text="Designates whether user has developer access."
    )
    can_access_files = models.BooleanField(
        "Files?",
        default=False,
        help_text="Designates whether user has file access."
    )
    allow_view = models.BooleanField(
        "View?",
        default=False,
        help_text="Designates whether user has view access to project."
    )

    def __str__(self):
        return f"{self.user} | {self.project}"

    # TODO(sean) UniqueConstraint seem to cause a bug as of Django 4.1, will investigate later.
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint("user", "project", name="app_profilemembership_uniq")
    #     ]


class NodeMembership(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    can_schedule = models.BooleanField(
        "Schedule?",
        default=False,
        help_text="Designates whether node allows scheduling."
    )
    can_develop = models.BooleanField(
        "Develop?",
        default=False,
        help_text="Designates whether node allows developer access."
    )
    can_access_files = models.BooleanField(
        "Files?",
        default=False,
        help_text="Designates whether node allows file access."
    )

    def __str__(self):
        return f"{self.node} | {self.project}"

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint("node", "project", name="app_nodemembership_uniq")
    #     ]
