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


class ProfileAdmin(admin.ModelAdmin):
    ordering = ("user__username",)
    inlines = (ProfileMembershipInline,)


class NodeAdmin(admin.ModelAdmin):
    ordering = ("vsn",)
    inlines = (NodeMembershipInline,)


class ProjectAdmin(admin.ModelAdmin):
    inlines = (ProfileMembershipInline, NodeMembershipInline)
    list_display = ("name", "number_of_members", "number_of_nodes")


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Project, ProjectAdmin)
