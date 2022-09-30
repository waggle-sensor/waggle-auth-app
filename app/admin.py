from django.contrib import admin
from .models import Profile, Node, Project, ProfileMembership, NodeMembership


class ProfileMembershipInline(admin.TabularInline):
    ordering = ("profile__user__username",)
    model = ProfileMembership
    extra = 0


class NodeMembershipInline(admin.TabularInline):
    ordering = ("node__vsn",)
    model = NodeMembership
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "name")
    search_fields = ("username", "name")
    inlines = (ProfileMembershipInline,)

    def username(self, profile):
        return profile.user.username


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("vsn", "mac")
    search_fields = ("vsn", "mac")
    ordering = ("vsn",)
    inlines = (NodeMembershipInline,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "number_of_members", "number_of_nodes")
    search_fields = ("name",)
    inlines = (ProfileMembershipInline, NodeMembershipInline)
