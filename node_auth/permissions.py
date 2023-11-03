from rest_framework.permissions import BasePermission

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated nodes.
    """

    def has_permission(self, request, view):
        try:
        	return request.user and request.user.vsn
        except:
        	return False