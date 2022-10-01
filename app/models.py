from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


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
