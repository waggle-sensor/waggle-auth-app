from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser
from app.models import Node, UserMembership, Project

class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user == obj))


class IsMatchingUsername(permissions.BasePermission):
    def has_permission(self, request, view):
        username = view.kwargs.get("username")
        return bool(request.user and (request.user.username == username))

class HasDevelopPermission(permissions.BasePermission):
    """
    Grants access only to authenticated users who have `can_develop=True`
    on *any* Project that includes the target Node (identified by its VSN).
    """
    message = "You do not have developer permission for this node."

    def has_permission(self, request, view):
        user = request.user

        # 0)  Superusers may always pass
        if getattr(user, "is_superuser", False):
            return True

        # 1) must be authenticated
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            self.message = "Authentication required."
            return False

        # 2) URL must include <vsn>
        vsn = view.kwargs.get("vsn")
        if not vsn:
            self.message = "VSN parameter missing from URL."
            return False

        # 3) node must exist
        try:
            node = Node.objects.get(vsn=vsn)
        except Node.DoesNotExist:
            self.message = f"Node with VSN '{vsn}' does not exist."
            return False

        # 4) projects that both contain the node *and* allow developer access
        projects = Project.objects.filter(
            nodemembership__node=node,
            nodemembership__can_develop=True,
        )

        # 5) does the user have developer rights in any of those projects?
        has_dev = UserMembership.objects.filter(
            user=user,
            project__in=projects,
            can_develop=True,
        ).exists()

        return has_dev
