from django.contrib.auth.models import *
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from .models import *
from .serializers import (
    ManifestSerializer,
    SensorViewSerializer,
    NodeBuildSerializer,
    ComputeSerializer,
    LorawanDeviceSerializer,
    LorawanConnectionSerializer,
    LorawanKeysSerializer,
    SensorHardwareCRUDSerializer,
    NodesSerializer
)
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from node_auth.mixins import NodeAuthMixin, NodeOwnedObjectsMixin
from app.authentication import TokenAuthentication as UserTokenAuthentication
from rest_framework.serializers import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from django.db.models import Q


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
    queryset = (
        SensorHardware.objects.all()
        .prefetch_related(
            "nodesensor_set",
            "nodesensor_set__node",
            "computesensor_set",
            "computesensor_set__scope",
            "computesensor_set__scope__node",
            "lorawandevice_set",
            "lorawandevice_set__lorawanconnections",
        )
        .order_by("hardware")
    )
    serializer_class = SensorViewSerializer
    lookup_field = "hardware"
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        res = super(SensorHardwareViewSet, self).list(request, *args, **kwargs)

        # if filtering, ignore sensors which aren't connected to nodes
        q = request.query_params
        if q.get("project") or q.get("phase"):
            res.data = filter(lambda o: len(o["vsns"]), res.data)

        return res

class SensorHardwareViewSet_CRUD(NodeAuthMixin, ModelViewSet):
    queryset = SensorHardware.objects.all()
    serializer_class = SensorHardwareCRUDSerializer
    lookup_field = "hw_model" #TODO: this can cause a "multiple response returned" server error on GET as hw_model is not unique - FL 01/29/2024
    authentication_classes = (NodeAuthMixin.authentication_classes[0],UserTokenAuthentication)
    permission_classes = (NodeAuthMixin.permission_classes[0]|IsAdminUser,)    

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
    queryset = LorawanDevice.objects.all()
    serializer_class = LorawanDeviceSerializer
    lookup_field = "deveui"


class LorawanConnectionView(NodeOwnedObjectsMixin, ModelViewSet):
    queryset = LorawanConnection.objects.all()
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
        try:
            node_vsn, lorawan_device_name, lorawan_device_deveui = lc_str.split("-")
        except ValueError:
            raise ValidationError(
                "Invalid lorawan_connection format. Use 'node-device_name-deveui'."
            )
        except Exception as e:
            raise ValidationError(
                f"Error: {e}"
            )
        lc = LorawanConnection.objects.get(
            node__vsn=node_vsn,
            lorawan_device__name=lorawan_device_name,
            lorawan_device__deveui=lorawan_device_deveui,
        )
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
            raise Http404  # <- should be 400, add later with error msg
        except ObjectDoesNotExist:
            raise Http404  # <- should be 400, add later with error msg

class NodesFilter(FilterSet):
    phase = CharFilter(method='or_filter')
    project__name = CharFilter(method='or_filter')

    def or_filter(self, queryset, name, value):
        # Split the value by comma to handle multiple conditions
        phases = value.split(',')
        # Use Q objects to construct an OR condition
        filter_condition = Q()
        for phase in phases:
            filter_condition |= Q(**{name: phase.strip()})
        return queryset.filter(filter_condition)

    class Meta:
        model = NodeData
        fields = ['project__name', 'phase']

class NodesViewSet(ReadOnlyModelViewSet):
    queryset = (
        NodeData.objects.all()
        .prefetch_related(
            "nodesensor_set",
            "compute_set",
            "lorawanconnections",
            "modem"
        )
        .order_by("vsn")
    )
    lookup_field = "vsn"
    serializer_class = NodesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NodesFilter
    