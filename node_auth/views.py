from .models import Token
from .serializers import AuthTokenSerializer
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet
from app.authentication import TokenAuthentication as UserTokenAuthentication

class TokenViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    authentication_classes = [UserTokenAuthentication]
    serializer_class = AuthTokenSerializer
    queryset = Token.objects.all().order_by("node__vsn")
    lookup_field = "node__vsn"