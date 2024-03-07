from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING
from node_auth import get_node_token_keyword, get_node_token_model
from .models import AnonymousNode

def get_node(request):
    """
    Get node instance using token in auth header. 
    If no node is retrieved, return an instance of `AnonymousNode`.
    """
    KEYWORD = get_node_token_keyword()

    auth = get_authorization_header(request).split()

    if not auth or auth[0].lower() != KEYWORD.lower().encode():
        return AnonymousNode()

    if len(auth) == 1:
        return AnonymousNode()
    elif len(auth) > 2:
        return AnonymousNode()

    try:
        token = auth[1].decode()
    except UnicodeError: # pragma: no cover
        return AnonymousNode()

    return authenticate_credentials(token)

def authenticate_credentials(key):
    TOKEN_MODEL = get_node_token_model()
    try:
        token = TOKEN_MODEL.objects.select_related("node").get(key=key)
    except TOKEN_MODEL.DoesNotExist:
        return AnonymousNode()

    if not token.node.is_active: 
        return AnonymousNode()

    return token.node

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