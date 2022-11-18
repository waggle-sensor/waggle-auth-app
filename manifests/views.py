from django.contrib.auth.models import *
from .models import *
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from .api.serializers import NodeSerializer
from django.http import HttpResponse

def index(request):
    return HttpResponse('SAGE Beekeeper-Manifest')


class NodeList(ListCreateAPIView):
    queryset = NodeData.objects.all().order_by("VSN")
    serializer_class = NodeSerializer


class NodeFilterList(RetrieveAPIView):

    queryset = NodeData.objects.all().order_by("VSN")
    serializer_class = NodeSerializer
    lookup_field = "VSN"