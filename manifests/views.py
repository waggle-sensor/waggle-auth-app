from django.contrib.auth.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from .models import *
from .serializers import NodeSerializer


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
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class NodeFilterList(RetrieveAPIView):
    queryset = NodeData.objects.all().order_by("vsn")
    serializer_class = NodeSerializer
    lookup_field = "vsn"
    permission_classes = [IsAuthenticatedOrReadOnly]
