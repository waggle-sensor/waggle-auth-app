from django.contrib.auth.models import *
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from .models import *
from .serializers import NodeSerializer


# BEFORE DOING ANY OF THIS, UPDATE THE TESTS TO INCLUDE ALL RELEVANT FIELDS!!!!

class NodeList(ListCreateAPIView):
    # queryset = NodeData.objects.all()
    queryset = NodeData.objects.all().prefetch_related(
        "compute_set__hardware__capabilities",
        "nodesensor_set__hardware",
        "nodesensor_set__labels",
        "resource_set__hardware__capabilities",
        "tags",
    )
    serializer_class = NodeSerializer
    permission_classes = [AllowAny]


class NodeFilterList(RetrieveAPIView):
    queryset = NodeData.objects.all()
    serializer_class = NodeSerializer
    lookup_field = "vsn"
    permission_classes = [AllowAny]
