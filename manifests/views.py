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
from rest_framework.response import Response
from rest_framework import status


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

class CreateLoRaWANDevice(CreateAPIView):
    serializer_class = LoRaWANDeviceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Retrieve the associated Node based on the 'vsn' provided in the serializer data
            vsn_data = serializer.validated_data['node']
            vsn = vsn_data['vsn']
            try:
                node = NodeData.objects.get(vsn=vsn)
            except NodeData.DoesNotExist:
                return Response({'message': f'Node with vsn {vsn} does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            # Create a LoRaWANDevice object based on serializer data and save to the database
            lorawan_device = LoRaWANDevice.objects.create(
                node=node,
                DevEUI=serializer.validated_data['DevEUI'],
                device_name=serializer.validated_data['device_name'],
                last_seen_at=serializer.validated_data['last_seen_at'],
                battery_level=serializer.validated_data['battery_level'],
                margin=request.data.get('margin'),
                expected_uplink_interval_sec = request.data.get('expected_uplink_interval_sec')
            )
            # Return a response
            return Response({'message': 'LoRaWANDevice created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)