from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from node_auth.serializers import AuthTokenSerializer
from node_auth.views import TokenViewSet
from unittest.mock import patch
from django.urls import reverse
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from node_auth import get_node_token_model, get_node_model
from rest_framework.test import APIRequestFactory
from rest_framework.authtoken.models import Token as UserToken

User = get_user_model()
Token = get_node_token_model()
Node = get_node_model()

class TokenViewSetTestCase(TestCase):
    def setUp(self):
        # Create necessary objects for testing
        self.factory = APIRequestFactory()
        self.admin_user = User.objects.create_superuser("test", "test", "test")
        self.admin_user_token = UserToken.objects.create(user=self.admin_user)
        self.Myvsn = "W001"
        self.mac = "111"
        self.node = Node.objects.create(vsn=self.Myvsn, mac=self.mac)
        self.node_2 = Node.objects.create(vsn="W002", mac="222")
        self.token = Token.objects.get(node=self.node)
        self.token_2 = Token.objects.get(node=self.node_2)

    @patch("node_auth.views.TokenViewSet.permission_classes", [AllowAny])
    def test_list_node_tokens(self):
        """Test token view for listing tokens"""

        # Create a request to retrieve the tokens
        url = reverse("node_auth:node-tokens-list")
        request = self.factory.get(url)

        # Use the token view to handle the request
        token_view = TokenViewSet.as_view({"get": "list"})
        response = token_view(request)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = AuthTokenSerializer(Token.objects.all(), many=True).data
        self.assertEqual(response.data, expected_data)

    @patch("node_auth.views.TokenViewSet.permission_classes", [AllowAny])
    def test_retrieve_node_token(self):
        """Test token view for retrieving a token"""

        # Create a request to retrieve the tokens
        url = reverse("node_auth:node-tokens-detail", kwargs={"node__vsn": self.Myvsn})
        request = self.factory.get(url)

        # Use the token view to handle the request
        token_view = TokenViewSet.as_view({"get": "retrieve"})
        response = token_view(request, node__vsn=self.Myvsn)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = AuthTokenSerializer(Token.objects.get(node=self.node)).data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_node_tokens_like_prod(self):
        """Test token view for listing tokens like it would be used in prod"""

        r = self.client.get(
            "/node-tokens/", HTTP_AUTHORIZATION=f"Sage {self.admin_user_token.key}"
        )

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.json()

        # Check the response status code and data
        expected_data = AuthTokenSerializer(Token.objects.all(), many=True).data
        self.assertEqual(results, expected_data)

    def test_list_node_token_like_prod(self):
        """Test token view for retrieving a token like it would be used in prod"""

        r = self.client.get(
            "/node-tokens/W001/", HTTP_AUTHORIZATION=f"Sage {self.admin_user_token.key}"
        )

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.json()

        # Check the response status code and data
        expected_data = AuthTokenSerializer(Token.objects.get(node=self.node)).data
        self.assertEqual(results, expected_data)