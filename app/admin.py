from django.contrib import admin
from .models import (
    Profile,
    Node,
    Project,
    ProfileMembership,
    NodeMembership,
)


class ProfileMembershipInline(admin.TabularInline):
    ordering = ("profile__user__username",)
    model = ProfileMembership
    extra = 0


class NodeMembershipInline(admin.TabularInline):
    ordering = ("node__vsn",)
    model = NodeMembership
    extra = 0


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ("user__username",)
    ordering = ("user__username",)
    inlines = (ProfileMembershipInline,)


class NodeAdmin(admin.ModelAdmin):
    list_display = ("vsn", "mac")
    search_fields = ("vsn", "mac")
    ordering = ("vsn",)
    inlines = (NodeMembershipInline,)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "number_of_members", "number_of_nodes")
    search_fields = ("name",)
    inlines = (ProfileMembershipInline, NodeMembershipInline)


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Project, ProjectAdmin)
