from django.test import TestCase
from app.models import Node
from node_auth.models import Token
from rest_framework.test import APIClient
from rest_framework.views import APIView
from node_auth.mixins import NodeAuthMixin, NodeOwnedObjectsMixin
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpRequest

class NodeTokenAuthTests(TestCase):
    """Token authentication"""
    model = None
    path = None
    header_prefix = 'node_auth '

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.vsn = 'W001'
        self.mac = '123'
        self.node = Node.objects.create(vsn=self.vsn, mac=self.mac)
        self.token = Token.objects.get(node=self.node)
        self.key = self.token.key

    def test_correct_token(self):
        """
        Test node token authentication using correct token
        """
        auth = self.header_prefix + self.key

        request = HttpRequest()
        request.method = 'POST'
        request.path = self.path
        request.data = {'example': 'example'}
        request.META['HTTP_AUTHORIZATION'] = auth

        # Create a simple view with the permission
        class TestView(NodeAuthMixin, APIView):
            def post(self, request, *args, **kwargs):
                return Response({"status": "success"}, status=status.HTTP_200_OK)

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request)

        assert response.status_code == status.HTTP_200_OK

    def test_wrong_token(self):
        """
        Test node token authentication using wrong token
        """
        auth = self.header_prefix + "123"

        request = HttpRequest()
        request.method = 'POST'
        request.path = self.path
        request.data = {'example': 'example'}
        request.META['HTTP_AUTHORIZATION'] = auth

        # Create a simple view with the permission
        class TestView(NodeAuthMixin, APIView):
            def post(self, request, *args, **kwargs):
                return Response({"status": "success"}, status=status.HTTP_200_OK)

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED