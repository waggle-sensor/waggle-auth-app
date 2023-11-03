from django.contrib.auth.models import *
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import *
from .serializers import (
    ManifestSerializer,
    SensorHardwareSerializer,
    NodeBuildSerializer,
    ComputeSerializer,
)

from node_auth.authentication import TokenAuthentication as NodeTokenAuthentication
from node_auth.permissions import IsAuthenticated as NodeIsAuthenticated, IsAuthenticated_ObjectLevel as NodeIsAuthenticated_ObjectLevel

class NodeOwnedObjectsMixin:
    """
    Allows access to objects associated to authenticated node. Order of operations:
    1) token authentication
    2) filter queryset to only include records associated with node
    3) checks object permission
    """
    authentication_classes = (NodeTokenAuthentication,)
    permission_classes = (NodeIsAuthenticated_ObjectLevel,)
    def get_queryset(self):
        nodeVSN = self.request.user.vsn
        queryset = super().get_queryset()
        return queryset.filter(vsn=nodeVSN)

class ManifestViewSet(NodeOwnedObjectsMixin,ReadOnlyModelViewSet):
    queryset = (
        NodeData.objects.all()
        .prefetch_related(
            "modem",
            "compute_set__hardware__capabilities",
            "nodesensor_set__hardware__capabilities",
            "nodesensor_set__labels",
            "compute_set__computesensor_set__scope",
            "compute_set__computesensor_set__hardware__capabilities",
            "compute_set__computesensor_set__labels",
            "resource_set__hardware__capabilities",
            "tags",
        )
        .order_by("vsn")
    )
    serializer_class = ManifestSerializer
    lookup_field = "vsn"
    permission_classes = [IsAuthenticatedOrReadOnly]

class ComputeViewSet(ReadOnlyModelViewSet):
    queryset = Compute.objects.all().order_by("node__vsn")
    serializer_class = ComputeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SensorHardwareViewSet(ReadOnlyModelViewSet):
    queryset = SensorHardware.objects.all().order_by("hardware")
    serializer_class = SensorHardwareSerializer
    lookup_field = "hardware"
    permission_classes = [IsAuthenticatedOrReadOnly]


class NodeBuildViewSet(ReadOnlyModelViewSet):
    queryset = (
        NodeBuild.objects.all()
        .prefetch_related("top_camera", "bottom_camera", "left_camera", "right_camera")
        .order_by("vsn")
    )
    serializer_class = NodeBuildSerializer
    lookup_field = "vsn"
    permission_classes = [IsAuthenticatedOrReadOnly]
