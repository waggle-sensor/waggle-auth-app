from django.contrib import admin
from .models import Profile, Node, Project, ProfileMembership, NodeMembership


class ProfileMembershipInline(admin.TabularInline):
    model = ProfileMembership
    extra = 0


class NodeMembershipInline(admin.TabularInline):
    model = NodeMembership
    extra = 0


admin.site.register(Profile, inlines=(ProfileMembershipInline,))
admin.site.register(Node, inlines=(NodeMembershipInline,))
admin.site.register(Project, inlines=(ProfileMembershipInline, NodeMembershipInline), list_display=("name", "number_of_members", "number_of_nodes"))
