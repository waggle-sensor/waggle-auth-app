from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING
from node_auth import get_token_keyword, get_token_model, get_node_model

class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """add the lazy node instance to request"""
        self.node_model = get_node_model()
        self.token_model = get_token_model()
        self.keyword = get_token_keyword()

        # Retrieve Node instance
        node_instance = SimpleLazyObject(lambda: self.get_node_instance(request))

        # Attach the 'node' attribute to the request
        request.node = node_instance
 
    def get_node_instance(self, request):
        """
        Get node instance using token in auth header. 
        If no node is retrieved, return an instance of `AnonymousNode`.
        """
        from .models import AnonymousNode

        auth = self.get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return AnonymousNode()

        if len(auth) == 1:
            return AnonymousNode()
        elif len(auth) > 2:
            return AnonymousNode()

        try:
            token = auth[1].decode()
        except UnicodeError:
            return AnonymousNode()

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        try:
            token = self.token_model.objects.select_related("node").get(key=key)
        except self.token_model.DoesNotExist:
            return AnonymousNode()

        if not token.node.is_active: 
            return AnonymousNode()

        return token.node

    @staticmethod
    def get_authorization_header(request):
        """
        Return request's 'Authorization:' header, as a bytestring.

        Hide some test client ickyness where the header can be unicode.
        """
        auth = request.META.get("HTTP_AUTHORIZATION", b"")
        if isinstance(auth, str):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth
