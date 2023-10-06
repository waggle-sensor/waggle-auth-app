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
    LoRaWANDeviceSerializer
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

@api_view(['POST'])
class CreateLoRaWANDevice(CreateAPIView):
    serializer = LoRaWANDeviceSerializer(data=request.data)
    if serializer.is_valid():
        # Create a LoRaWANDevice object based on serializer data and save to db
        lorawan_device = LoRaWANDevice.objects.create(
            node = serializer.validated_data['node'],
            device_id = serializer.validated_data['device_id'],
            device_name = serializer.validated_data['device_name'],
            last_seen_at = serializer.validated_data['last_seen_at'],
            battery_level = serializer.validated_data['battery_level'],
            margin=data.get('margin')
        )
        # Save the object to the database
        # Return a response
        return Response({'message': 'LoRaWANDevice created successfully'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)