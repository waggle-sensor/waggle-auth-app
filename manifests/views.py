from django.contrib.auth.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import *
from .serializers import (
    ManifestSerializer,
    SensorHardwareSerializer,
    NodeBuildSerializer,
    ComputeSerializer,
)


class ManifestViewSet(ReadOnlyModelViewSet):
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

class CreateLoRaWANSensorAPIView(CreateAPIView):
    queryset = LoRaWANSensor.objects.all()
    serializer_class = LoRaWANSensorSerializer