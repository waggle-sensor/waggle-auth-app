from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


class ExpiringTokenAuthentication(TokenAuthentication):

    keyword = "Sage"

    def authenticate_credentials(self, key):
        try:
            token: Token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("token is invalid")
        
        if not token.user.is_active:
            raise AuthenticationFailed("user is not active")

        if age(token.created) > timedelta(seconds=settings.TOKEN_EXPIRE_SECONDS):
            raise AuthenticationFailed("token is expired")

        return token.user, token


def age(t):
    return timezone.now() - t
