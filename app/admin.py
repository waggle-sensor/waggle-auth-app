from django.contrib import admin
from .models import Node, Project, UserMembership, NodeMembership


class UserMembershipInline(admin.TabularInline):
    ordering = ("user__username",)
    model = UserMembership
    extra = 0


class NodeMembershipInline(admin.TabularInline):
    ordering = ("node__vsn",)
    model = NodeMembership
    extra = 0


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("vsn", "mac")
    search_fields = ("vsn", "mac")
    ordering = ("vsn",)
    inlines = (NodeMembershipInline,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "number_of_users", "number_of_nodes")
    search_fields = ("name",)
    inlines = (UserMembershipInline, NodeMembershipInline)
