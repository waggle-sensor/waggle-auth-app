from django.test import TestCase
from django.test.client import RequestFactory
from node_auth.contrib.auth import get_node as auth_get_node, authenticate_credentials
from node_auth.contrib.auth.models import AnonymousNode
from django.contrib.auth import get_user_model
from node_auth import get_node_token_keyword, get_node_model, get_node_token_model
from unittest.mock import patch, Mock

Node = get_node_model()
Token = get_node_token_model()

class Middleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.vsn = 'W001'
        self.mac = '111'
        self.node = Node.objects.create(vsn=self.vsn, mac=self.mac)
        self.token = Token.objects.get(node=self.node)
        self.auth_header = get_node_token_keyword() + " " + self.token.key

    def tearDown(self):
        Node.objects.all().delete()
        Token.objects.all().delete()

    def test_get_node_happy_path(self):
        """
        Test that get node function returns node associated with token
        """
        request = self.factory.get("/", HTTP_AUTHORIZATION=self.auth_header)
        response = auth_get_node(request)
        self.assertEqual(response, self.node)

    def test_get_node_with_no_auth_header(self):
        """
        Test that get node function returns anonymous node when request has no auth header
        """
        request = self.factory.get("/")
        response = auth_get_node(request)
        self.assertEqual(response,AnonymousNode())

    def test_get_node_with_no_token(self):
        """
        Test that get node function returns anonymous node when request has no token
        """
        request = self.factory.get("/", HTTP_AUTHORIZATION=get_node_token_keyword())
        response = auth_get_node(request)
        self.assertEqual(response,AnonymousNode())

    def test_get_node_with_extra_spaces(self):
        """
        Test that get node function returns anonymous node when request has extra spaces
        """
        request = self.factory.get("/", HTTP_AUTHORIZATION=self.auth_header + " test")
        response = auth_get_node(request)
        self.assertEqual(response,AnonymousNode())

    def test_authenticate_credentials_happy_path(self):
        """
        Test that authenticate_credentials returns node associated with token 
        """
        response = authenticate_credentials(self.token.key)
        self.assertEqual(response, self.node)

    def test_authenticate_credentials_nonexistent_token(self):
        """
        Test that authenticate_credentials returns anonymous node when token does not exist
        """
        response = authenticate_credentials("invalid_token")
        self.assertEqual(response, AnonymousNode())

    def test_authenticate_credentials_node_inactive(self):
        """
        Test that authenticate_credentials returns anonymous node when node is inactive
        """
        inactive_node = Node.objects.create(vsn="123", mac="123", is_active=False)
        inactive_token = Token.objects.get(node=inactive_node)
        response = authenticate_credentials(inactive_token.key)
        self.assertEqual(response, AnonymousNode())

if __name__ == "__main__":
    unittest.main()