from django.db import models
from django.contrib.auth.models import User
# TODO add date created / updated type fields to all items


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    def number_of_members(self):
        return self.profile_set.count()

    def number_of_nodes(self):
        return self.node_set.count()


class Node(models.Model):
    vsn = models.CharField("VSN", max_length=10, unique=True)
    mac = models.CharField("MAC", max_length=16, unique=True, null=True)
    projects = models.ManyToManyField(Project, through="NodeMembership")

    def __str__(self):
        return self.vsn


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    projects = models.ManyToManyField(Project, through="ProfileMembership")

    def __str__(self):
        return str(self.user)


class ProfileMembership(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
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
        return f"{self.profile} | {self.project}"

    class Meta:
        constraints = [
            models.UniqueConstraint("profile", "project", name="app_profilemembership_uniq")
        ]


class NodeMembership(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
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

    class Meta:
        constraints = [
            models.UniqueConstraint("node", "project", name="app_nodemembership_uniq")
        ]
