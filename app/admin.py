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

# admin.site.register(
#     ProfileMembership,
#     list_display=("profile", "project", "can_schedule", "can_develop", "can_access_files"),
#     list_filter=("profile", "project"),
# )

# all this would be much easier if permissions were directly inhereted from a team, of course...

# Team
# Sage Admin
# Sage
# Dawn Admin

# can i define a custom form for this??? like a more efficient click with drop down list?
# we can define something similar for group permissions
