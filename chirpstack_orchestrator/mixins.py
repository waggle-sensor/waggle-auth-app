"""
ChirpStack Orchestrator mixins to be used in views.
"""
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from app.authentication import TokenAuthentication as UserTokenAuthentication
from app.permissions import HasDevelopPermission
import chirpstack_orchestrator.utils as utils

class ChirpstackMixin:
    """
    Mixin to provide common functionality for ChirpStack views.
    """
    authentication_classes = [SessionAuthentication, UserTokenAuthentication]
    permission_classes = [IsAuthenticated, HasDevelopPermission]

    def _client(self, vsn): return utils.get_chirpstack_client(vsn)
    def _todict(self, proto) -> dict:
        if type(proto) == list:
            return utils.protos_to_dicts(proto)
        return utils.proto_to_dict(proto)