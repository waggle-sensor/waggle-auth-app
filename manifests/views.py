from django.contrib.auth.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import *
from .serializers import ManifestSerializer, SensorHardwareSerializer


class NodeList(ListAPIView):
    queryset = NodeData.objects.all().prefetch_related(
        "compute_set__hardware__capabilities",

        "nodesensor_set__hardware__capabilities",
        "nodesensor_set__labels",

        "compute_set__computesensor_set__scope",
        "compute_set__computesensor_set__hardware__capabilities",
        "compute_set__computesensor_set__labels",

        "resource_set__hardware__capabilities",

        "tags",
    ).order_by("vsn")
    serializer_class = ManifestSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class NodeFilterList(RetrieveAPIView):
    queryset = NodeData.objects.all().prefetch_related(
        "compute_set__hardware__capabilities",

        "nodesensor_set__hardware__capabilities",
        "nodesensor_set__labels",

        "compute_set__computesensor_set__scope",
        "compute_set__computesensor_set__hardware__capabilities",
        "compute_set__computesensor_set__labels",

        "resource_set__hardware__capabilities",

        "tags",
    )
    serializer_class = ManifestSerializer
    lookup_field = "vsn"
    permission_classes = [IsAuthenticatedOrReadOnly]


class SensorHardwareListView(ListAPIView):
    queryset = SensorHardware.objects.all()
    serializer_class = SensorHardwareSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SensorHardwareDetailView(RetrieveAPIView):
    queryset = SensorHardware.objects.all()
    serializer_class = SensorHardwareSerializer
    lookup_field = "hardware"
    permission_classes = [IsAuthenticatedOrReadOnly]
