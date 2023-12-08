from django.contrib.auth.models import *
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.generics import (
    RetrieveAPIView,
    CreateAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from .models import *
from .serializers import (
    ManifestSerializer,
    SensorHardwareSerializer,
    NodeBuildSerializer,
    ComputeSerializer,
    LorawanDeviceSerializer,
    LorawanConnectionSerializer,
    LorawanKeysSerializer,
)
from rest_framework.response import Response  
from rest_framework import status
from django.db import IntegrityError 
from node_auth.mixins import NodeAuthMixin, NodeOwnedObjectsMixin


class ManifestViewSet(ReadOnlyModelViewSet):
    serializer_class = ManifestSerializer
    lookup_field = "vsn"
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = (
            NodeData.objects.all()
            .prefetch_related(
                "project",
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

        project = self.request.query_params.get("project")
        if project:
            queryset = queryset.filter(project__name__iexact=project)

        return queryset

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

class LorawanDeviceView(NodeAuthMixin, ModelViewSet):
    serializer_class = LorawanDeviceSerializer
    queryset = LorawanDevice.objects.all()
    lookup_field = "deveui"

class LorawanConnectionView(NodeOwnedObjectsMixin, ModelViewSet):
    serializer_class = LorawanConnectionSerializer
    vsn_field = "node__vsn"

    def get_object(self):
        # Get the 'node_vsn' and 'lorawan_deveui' from the URL
        node_vsn = self.kwargs["node_vsn"]
        lorawan_deveui = self.kwargs["lorawan_deveui"]

        # Retrieve the LorawanConnection instance based on the lookup fields
        try:
            lorawan_connection = LorawanConnection.objects.get(
                node__vsn=node_vsn, lorawan_device__deveui=lorawan_deveui
            )
            self.check_object_permissions(self.request, lorawan_connection.node)
            return lorawan_connection
        except LorawanConnection.DoesNotExist:
            raise Http404

class LorawanKeysView(NodeOwnedObjectsMixin, ModelViewSet):
    serializer_class = LorawanKeysSerializer
    lookup_field = "lorawan_connection"
    vsn_field = "lorawan_connection__node__vsn"
    foreign_key_name = "lorawan_connection__node"

    def vsn_get_func(self, obj, request, foreign_key_name):
        model, field = foreign_key_name.split("__")
        lc_str = request.data.get(model)
        node_vsn, lorawan_device_name, lorawan_device_deveui = lc_str.split('-')
        lc = LorawanConnection.objects.get(node__vsn=node_vsn, lorawan_device__device_name=lorawan_device_name, lorawan_device__deveui=lorawan_device_deveui)
        if lc:
            node_obj = getattr(lc, field)
            return node_obj.vsn
        else:
            return None

    def get_object(self):
        # Get the 'node_vsn' and 'lorawan_deveui' from the URL
        node_vsn = self.kwargs["node_vsn"]
        lorawan_deveui = self.kwargs["lorawan_deveui"]

        # Retrieve the LorawanConnection instance based on the lookup fields
        try:
            lorawan_connection = LorawanConnection.objects.get(
                node__vsn=node_vsn, lorawan_device__deveui=lorawan_deveui
            )
            self.check_object_permissions(self.request, lorawan_connection.node)
            return lorawan_connection.lorawankey
        except LorawanConnection.DoesNotExist:
            raise Http404 #<- should be 400, add later with error msg
        except ObjectDoesNotExist:
            raise Http404 #<- should be 400, add later with error msg