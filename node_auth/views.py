from rest_framework import parsers, renderers
from .models import Token
from .serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView

#delete this? we dont want to obtain the auth token by vsn. Defeats the purpose of adding a token - francisco lozano
class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    # def get_serializer_context(self):
    #     return {
    #         'request': self.request,
    #         'format': self.format_kwarg,
    #         'view': self
    #     }

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['context'] = self.get_serializer_context()
    #     return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        #serializer = self.get_serializer(data=request.data)
        serializer =self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        node = serializer.validated_data['node']
        token, created = Token.objects.get_or_create(node=node)
        return Response({'token': token.key})