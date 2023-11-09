from django.contrib.auth.models import *
from django.http import Http404
from rest_framework.generics import (
    RetrieveAPIView,
    CreateAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import *
from .serializers import (
    ManifestSerializer,
    SensorHardwareSerializer,
    NodeBuildSerializer,
    ComputeSerializer,
    LorawanDeviceSerializer,
    LorawanConnectionSerializer, NodesSerializer,
)
from rest_framework.response import Response
from rest_framework import status


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


class LorawanDeviceView(CreateAPIView, UpdateAPIView, RetrieveAPIView):
    serializer_class = LorawanDeviceSerializer
    queryset = LorawanDevice.objects.all()
    lookup_field = "deveui"
    permission_classes = [
        IsAdminUser
    ]  # adding this for now until node authentication architecture is created

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Create a LorawanDevice object based on serializer data and save to the database
            LorawanDevice.objects.create(**serializer.validated_data)

            # Return a response
            return Response(
                {"message": "LorawanDevice created successfully"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            updated_data = {}

            # update the Lorawan object based on serializer data
            for attr, value in serializer.validated_data.items():
                updated_data[attr] = value

            serializer.save(**updated_data)

            # Return a response
            return Response(
                {"message": "LorawanDevice updated successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LorawanConnectionView(CreateAPIView, UpdateAPIView, RetrieveAPIView):
    serializer_class = LorawanConnectionSerializer
    queryset = LorawanConnection.objects.all()
    permission_classes = [
        IsAdminUser
    ]  # adding this for now until node authentication architecture is created

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self):
        # Get the 'node_vsn' and 'lorawan_deveui' from the URL
        node_vsn = self.kwargs["node_vsn"]
        lorawan_deveui = self.kwargs["lorawan_deveui"]

        # Retrieve the LorawanConnection instance based on the lookup fields
        try:
            lorawan_connection = LorawanConnection.objects.get(
                node__vsn=node_vsn, lorawan_device__deveui=lorawan_deveui
            )
            return lorawan_connection
        except LorawanConnection.DoesNotExist:
            raise Http404

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_record = {}

            # Create a LorawanConnection object based on serializer data and save to the database
            for attr, value in serializer.validated_data.items():
                if (
                        attr == "node"
                ):  # Retrieve the associated Node based on the 'vsn' provided in the serializer data
                    vsn_data = value
                    vsn = vsn_data["vsn"]
                    try:
                        node = NodeData.objects.get(vsn=vsn)
                    except NodeData.DoesNotExist:
                        return Response(
                            {"message": f"Node with vsn {vsn} does not exist"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        new_record["node"] = node
                elif (
                        attr == "lorawan_device"
                ):  # Retrieve the associated lorawan_device based on the 'deveui' provided in the serializer data
                    device_data = value
                    deveui = device_data["deveui"]
                    try:
                        device = LorawanDevice.objects.get(deveui=deveui)
                    except LorawanDevice.DoesNotExist:
                        return Response(
                            {
                                "message": f"Lorawan Device with deveui {deveui} does not exist"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        new_record["lorawan_device"] = device
                else:
                    new_record[attr] = value

            LorawanConnection.objects.create(**new_record)

            # Return a response
            return Response(
                {"message": "LorawanConnection created successfully"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            updated_data = {}

            # update the Lorawan object based on serializer data
            for attr, value in serializer.validated_data.items():
                if (
                        attr == "node"
                ):  # Retrieve the associated Node based on the 'vsn' provided in the serializer data
                    vsn_data = value
                    vsn = vsn_data["vsn"]
                    try:
                        node = NodeData.objects.get(vsn=vsn)
                    except NodeData.DoesNotExist:
                        return Response(
                            {"message": f"Node with vsn {vsn} does not exist"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        updated_data["node"] = node
                elif (
                        attr == "lorawan_device"
                ):  # Retrieve the associated lorawan_device based on the 'deveui' provided in the serializer data
                    device_data = value
                    deveui = device_data["deveui"]
                    try:
                        device = LorawanDevice.objects.get(deveui=deveui)
                    except LorawanDevice.DoesNotExist:
                        return Response(
                            {
                                "message": f"Lorawan Device with deveui {deveui} does not exist"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        updated_data["lorawan_device"] = device
                else:
                    updated_data[attr] = value

            serializer.save(**updated_data)

            # Return a response
            return Response(
                {"message": "LorawanConnection updated successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NodesViewSet(ReadOnlyModelViewSet):
    queryset = NodeData.objects.all()
    serializer_class = NodesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
