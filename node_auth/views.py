# from rest_framework import parsers, renderers
# from .serializers import AuthTokenSerializer
# from rest_framework.permissions import IsAdminUser
# from rest_framework.response import Response
# from rest_framework.views import APIView
from node_auth.mixins import NodeOwnedObjectsMixin
from rest_framework.viewsets import ReadOnlyModelViewSet
from node_auth.serializers import WireGuardSerializer

class WireGuardView(NodeOwnedObjectsMixin, ReadOnlyModelViewSet):
    serializer_class = WireGuardSerializer
    vsn_field = "node__vsn"

# class ObtainAuthToken(APIView):
#     throttle_classes = ()
#     permission_classes = IsAdminUser
#     parser_classes = (
#         parsers.FormParser,
#         parsers.MultiPartParser,
#         parsers.JSONParser,
#     )
#     renderer_classes = (renderers.JSONRenderer,)
#     serializer_class = AuthTokenSerializer

#     def post(self, request, *args, **kwargs):
#         # serializer = self.get_serializer(data=request.data)
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         node = serializer.validated_data["node"]
#         token, created = Token.objects.get_or_create(node=node)
#         return Response({"token": token.key})
