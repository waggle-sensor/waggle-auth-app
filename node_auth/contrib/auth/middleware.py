from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from node_auth.contrib.auth import get_node as auth_get_node

def get_node(request):
    return auth_get_node(request)

class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """add the lazy node instance to request"""

        # Retrieve Node instance
        node_instance = SimpleLazyObject(lambda: get_node(request))

        # Attach the 'node' attribute to the request
        request.node = node_instance
