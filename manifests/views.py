from django.contrib.auth.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import *
from .serializers import (
    ManifestSerializer,
    SensorHardwareSerializer,
    NodeBuildSerializer,
    ComputeSerializer,
    LorawanDeviceSerializer
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

class LorawanDeviceView(CreateAPIView, UpdateAPIView):
    serializer_class = LorawanDeviceSerializer
    queryset = LoRaWANDevice.objects.all()
    lookup_field = 'DevEUI'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_record={}
            # Retrieve the associated Node based on the 'vsn' provided in the serializer data
            vsn_data = serializer.validated_data.pop('node')
            vsn = vsn_data['vsn']
            try:
                node = NodeData.objects.get(vsn=vsn)
            except NodeData.DoesNotExist:
                return Response({'message': f'Node with vsn {vsn} does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                new_record['node']=node

            # Create a LoRaWANDevice object based on serializer data and save to the database
            for attr,value in serializer.validated_data.items():
                new_record[attr]=value
            lorawan_device = LoRaWANDevice.objects.create(**new_record)

            # Return a response
            return Response({'message': 'LoRaWANDevice created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            updated_data={}
            
            #update the LoRaWAN object based on serializer data
            for attr,value in serializer.validated_data.items():

                if attr == 'node': # Retrieve the associated Node based on the 'vsn' provided in the serializer data
                    vsn_data = value
                    vsn = vsn_data['vsn']
                    try:
                        node = NodeData.objects.get(vsn=vsn)
                    except NodeData.DoesNotExist:
                        return Response({'message': f'Node with vsn {vsn} does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        updated_data['node']=node
                else:
                    updated_data[attr]=value

            serializer.save(**updated_data)

            # Return a response
            return Response({'message': 'LoRaWANDevice updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)