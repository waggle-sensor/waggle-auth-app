from django.contrib.auth.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from .models import *
from .serializers import NodeSerializer


class NodeList(ListAPIView):
    queryset = NodeData.objects.all().order_by("vsn")
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class NodeFilterList(RetrieveAPIView):
    queryset = NodeData.objects.all().order_by("vsn")
    serializer_class = NodeSerializer
    lookup_field = "vsn"
    permission_classes = [IsAuthenticatedOrReadOnly]
