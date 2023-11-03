from rest_framework.permissions import BasePermission

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated nodes.
    """

    def has_permission(self, request, view):
        """
        Checks for view level permissions.
        """
        node = request.user
        try:
        	return node and node.vsn
        except:
        	return False

class IsAuthenticated_ObjectLevel(BasePermission):
    """
    Allows access only to records associated to the authenticated node.
    """

    def has_permission(self, request, view):
        """
        Checks for view level permissions.
        """
        node = request.user
        try:
        	return node and node.vsn
        except:
        	return False

    def has_object_permission(self, request, view, obj):
        """
        Checks for object level permissions.
        """
        node = request.user

        # Instance must have an attribute named `vsn`.
        return obj.vsn == node.vsn