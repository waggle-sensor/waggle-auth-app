import unittest
from django.test import TestCase
from app.models import Node
from rest_framework.test import APIRequestFactory
from rest_framework import exceptions
from node_auth.authentication import TokenAuthentication, BaseAuthentication
from unittest.mock import patch, Mock

class TestTokenAuthentication(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.vsn = 'W001'
        self.mac = '111'
        self.node = Node.objects.create(vsn=self.vsn, mac=self.mac)
        self.token = TokenAuthentication.model.objects.get(node=self.node)

    def tearDown(self):
        Node.objects.all().delete()
        TokenAuthentication.model.objects.all().delete()

    def test_authenticate_valid_token(self):
        """
        Test that authenticate method returns a valid node and token for a valid token.
        """
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"node_auth {self.token.key}")
        authentication = TokenAuthentication()

        node, token = authentication.authenticate(request)

        self.assertEqual(node, self.node)
        self.assertEqual(token, self.token)

    def test_authenticate_invalid_token(self):
        """
        Test that authenticate method raises AuthenticationFailed for an invalid token.
        """
        request = self.factory.get("/", HTTP_AUTHORIZATION="node_auth invalidtoken")
        authentication = TokenAuthentication()
        with self.assertRaises(exceptions.AuthenticationFailed):
            authentication.authenticate(request)

    def test_authenticate_credentials(self):
        """
        Test authenticate_credentials method returns a valid user and token for a valid key.
        """
        authentication = TokenAuthentication()
        node, token = authentication.authenticate_credentials(self.token.key)

        # Assertions
        self.assertEqual(node, self.node)
        self.assertEqual(token, self.token)

    def test_authenticate_credentials_invalid_key(self):
        """
        Test authenticate_credentials method raises AuthenticationFailed for an invalid key.
        """
        authentication = TokenAuthentication()
        with self.assertRaises(exceptions.AuthenticationFailed):
            authentication.authenticate_credentials("invalidkey")

    def test_authenticate_header(self):
        """
        Test that authenticate_header method returns the correct keyword.
        """
        request = self.factory.get("/")
        authentication = TokenAuthentication()
        result = authentication.authenticate_header(request)
        self.assertEqual(result, "node_auth")

    def test_baseauth_authenticate_method(self):
        base_auth = BaseAuthentication()
        mock_request = Mock()
        with self.assertRaises(NotImplementedError):
            base_auth.authenticate(mock_request)

    def test_baseauth_authenticateheader_method(self):
        base_auth = BaseAuthentication()
        mock_request = Mock()
        result = base_auth.authenticate_header(mock_request)
        self.assertIsNone(result)

    @patch('node_auth.authentication.get_authorization_header')
    def test_authenticate_method_returns_none_invalid_header(self, mock_get_authorization_header):
        token_auth = TokenAuthentication()
        mock_request = Mock()

        # Mock the get_authorization_header function to return an invalid header
        mock_get_authorization_header.return_value = b'Bearer invalid_token'

        result = token_auth.authenticate(mock_request)

        self.assertIsNone(result)

    @patch('node_auth.authentication.get_authorization_header')
    def test_authenticate_invalid_token_header_no_credentials(self, mock_get_authorization_header):
        token_auth = TokenAuthentication()
        mock_request = Mock()

        # Mock the get_authorization_header function to return only keyword
        mock_get_authorization_header.return_value = b'node_auth'

        with self.assertRaises(exceptions.AuthenticationFailed) as context:
            token_auth.authenticate(mock_request)

    @patch('node_auth.authentication.get_authorization_header')
    def test_authenticate_invalid_token_header_with_spaces(self, mock_get_authorization_header):
        token_auth = TokenAuthentication()
        mock_request = Mock()

        # Mock the get_authorization_header function to return an invalid header with spaces
        mock_get_authorization_header.return_value = b'node_auth token with spaces'

        with self.assertRaises(exceptions.AuthenticationFailed) as context:
            token_auth.authenticate(mock_request)

    @patch('node_auth.authentication.get_authorization_header')
    def test_authenticate_invalid_token_header_with_invalid_char(self, mock_get_authorization_header):
        token_auth = TokenAuthentication()
        mock_request = Mock()

        # Mock the get_authorization_header function to return a token with invalid characters
        mock_get_authorization_header.return_value = b'node_auth \x00'

        with self.assertRaises(exceptions.AuthenticationFailed) as context:
            token_auth.authenticate(mock_request)

if __name__ == "__main__":
    unittest.main()
