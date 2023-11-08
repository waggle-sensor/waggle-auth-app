from node_auth.authentication import TokenAuthentication
from node_auth.permissions import IsAuthenticated, IsAuthenticated_ObjectLevel, OnlyAssociateToSelf

class NodeAuthMixin:
    """
    Allows access to authenticated node:
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

class NodeOwnedObjectsMixin(NodeAuthMixin):
    """
    Allows access to ONLY objects associated with the authenticated node. Order of operations:
    1) Token authentication
    2) Filter queryset to only include records associated with the node (reference your model's vsn field)
    3) Check object permission (custom views, you'll need to make sure you check the object level permission checks yourself)
        - self.check_object_permissions(request, node_obj)
    """
    vsn_field = 'vsn'  # Default vsn field name
    foreign_key_name = 'node' # default node foreign key
    permission_classes = [IsAuthenticated_ObjectLevel(foreign_key_name), OnlyAssociateToSelf(foreign_key_name)]

    def get_queryset(self):
        nodeVSN = self.request.user.vsn
        queryset = super().get_queryset()
        return queryset.filter(**{f'{self.vsn_field}': nodeVSN})