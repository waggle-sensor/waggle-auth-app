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
    Defaulted to use 'node' as foreign key name
    """

    def __init__(self, foreign_key_name='node'):
        self.foreign_key_name = foreign_key_name

    #return the object when called. Avoids TypeError when used in permission_classes
    def __call__(self):
        return self

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

        # Check object-level permissions here using the user-specified foreign key name
        if hasattr(obj,'vsn'):
            return obj.vsn == node.vsn
        else:
            node_obj = getattr(obj, self.foreign_key_name)
            return node_obj.vsn == node.vsn

class OnlyAssociateToSelf(BasePermission):
    """
    Permission to only allow authenticated Nodes to create objects associated to itself.
    Defaulted to use 'node' as foreign key name
    """

    def __init__(self, foreign_key_name='node'):
        self.foreign_key_name = foreign_key_name

    #return the object when called. Avoids TypeError when used in permission_classes
    def __call__(self):
        return self

    def has_permission(self, request, view):

        node = request.user

        # Check if the request is POST
        if request.method == 'POST':
            # Check if object is associated to self
            obj_vsn = request.data.get(self.foreign_key_name)
            return obj_vsn == node.vsn

        # For other requests, allow access based on user's own vsn
        try:
            return node and node.vsn
        except:
            return False