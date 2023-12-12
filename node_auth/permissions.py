from rest_framework.permissions import BasePermission
from rest_framework import exceptions


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated nodes.
    """

    def has_permission(self, request, view):
        """
        Checks for view level permissions.
        """
        try:
            node = request.node
        except:
        	raise exceptions.AuthenticationFailed(detail='Could not get node from request')

        return node and node.vsn

class IsAuthenticated_ObjectLevel(IsAuthenticated):
    """
    Allows access only to records associated to the authenticated node.
    Defaulted to use 'node' as foreign key name
    """

    #return the object when called. Avoids TypeError when used in permission_classes
    def __call__(self):
        return self

    def has_object_permission(self, request, view, obj):
        """
        Checks for object level permissions.
        """
        node = request.node

        # Check object-level permissions here using the user-specified foreign key name
        foreign_key_name = getattr(view, 'foreign_key_name', 'node')
        if hasattr(obj, 'vsn'):
            return obj.vsn == node.vsn
        else:
            attributes = foreign_key_name.split('__')
            record = obj
            for attr in attributes:
                try:
                    record = getattr(record, attr)
                except AttributeError:
                    raise exceptions.ParseError(detail='Nested relationship error, could not get node table')
            return record.vsn == node.vsn

class OnlyCreateToSelf(BasePermission):
    """
    Permission to only allow authenticated Nodes to create objects associated to itself.
    Defaulted to use 'node' as foreign key name. 
    """

    #return the object when called. Avoids TypeError when used in permission_classes
    def __call__(self):
        return self

    def has_permission(self, request, view):

        try:
            node = request.node
        except:
        	raise exceptions.AuthenticationFailed(detail='Could not get node from request')

        # Check object-level permissions here using the user-specified foreign key name
        foreign_key_name = getattr(view, 'foreign_key_name', 'node')

        # Check if the request is POST
        if request.method == 'POST':
            # Check if object is associated to self
            vsn_get_func = getattr(view, 'vsn_get_func', None)
            if callable(vsn_get_func):
                obj_vsn = vsn_get_func(self, request, foreign_key_name)
            else:
                obj_vsn = self.default(self, request, foreign_key_name)
            return obj_vsn == node.vsn

        # For other requests, allow access based on user's own vsn
        return node and node.vsn


    @staticmethod
    def default(self, request, foreign_key_name):
        return request.data.get(foreign_key_name)