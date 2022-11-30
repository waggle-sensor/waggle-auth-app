from django.contrib.auth.models import *
from .models import *
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from .api.serializers import NodeSerializer


class NodeList(ListCreateAPIView):
    queryset = NodeData.objects.all().order_by("vsn")
    serializer_class = NodeSerializer
    permission_classes = [AllowAny]


class NodeFilterList(RetrieveAPIView):
    queryset = NodeData.objects.all().order_by("vsn")
    serializer_class = NodeSerializer
    lookup_field = "vsn"
    permission_classes = [AllowAny]
