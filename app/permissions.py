from rest_framework import permissions


class IsSelf(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user == obj))


class IsMatchingUsername(permissions.BasePermission):
    # TODO Figure out how to do this in general. This is a hack to apply permissions
    # to the user access view based on username in the URL.

    def has_permission(self, request, view):
        username = view.kwargs.get("username")
        return bool(request.user and (request.user.username == username))
