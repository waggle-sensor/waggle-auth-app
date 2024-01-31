from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from .models import User, Node, Project, UserMembership, NodeMembership


class UserMembershipInline(admin.TabularInline):
    ordering = ("user__username",)
    model = UserMembership
    extra = 0
    autocomplete_fields = ["user", "project"]


class NodeMembershipInline(admin.TabularInline):
    ordering = ("node__vsn",)
    model = NodeMembership
    extra = 0
    autocomplete_fields = ["node", "project"]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "name",
                    "email",
                    "organization",
                    "department",
                    "bio",
                    "ssh_public_keys",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_approved",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("username", "name", "email", "is_superuser", "is_approved")
    list_filter = ("is_superuser", "is_approved")
    search_fields = ("username", "name")
    inlines = (UserMembershipInline,)


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("vsn", "mac", "commissioning_date", "files_public")
    list_filter = ("files_public",)
    search_fields = ("vsn", "mac")
    ordering = ("vsn",)
    inlines = (NodeMembershipInline,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "number_of_users", "number_of_nodes")
    search_fields = ("name",)
    inlines = (UserMembershipInline, NodeMembershipInline)
