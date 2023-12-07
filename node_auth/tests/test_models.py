from django.test import TestCase
from node_auth.models import Token
import unittest
from unittest.mock import patch
from node_auth.models import Token
from node_auth import get_token_keyword, get_node_model, get_token_model
from django.core.exceptions import ImproperlyConfigured

class test_TokenModel(TestCase):

    @patch("node_auth.models.os.urandom")
    def test_generate_key(self, mock_urandom):
        """ Test generation of key function """
        # Mock the os.urandom method to control the random bytes generated
        mock_urandom.return_value = b"\x01\x23\x45\x67\x89\xab\xcd\xef"

        # Call the method under test
        key = Token.generate_key()

        self.assertEqual(key, "0123456789abcdef")  # Expected hex value based on the mocked os.urandom result

    def test_str_method(self):
        """ Test str of model """
        # Create an instance of the Token model
        token_instance = Token(key="test_key")

        result = str(token_instance)

        self.assertEqual(result, "test_key")

class get_functions(TestCase):

    @patch('node_auth.settings.AUTH_NODE_MODEL', 'invalid_model_format')
    def test_get_node_model_ValueError(self):
        """
        test get_node_model raises ImproperlyConfigured for value error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_node_model()

    @patch('node_auth.settings.AUTH_NODE_MODEL', 'nonexistent_app.NonexistentModel')
    def test_get_node_model_lookup_error(self):
        """
        test get_node_model raises ImproperlyConfigured for lookup error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_node_model()

    @patch('node_auth.settings.AUTH_NODE_TOKEN_MODEL', 'invalid_model_format')
    def test_get_token_model_ValueError(self):
        """
        test get_token_model raises ImproperlyConfigured for value error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_token_model()

    @patch('node_auth.settings.AUTH_NODE_TOKEN_MODEL', 'nonexistent_app.NonexistentModel')
    def test_get_token_model_lookup_error(self):
        """
        test get_token_model raises ImproperlyConfigured for lookup error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_token_model()

    @patch('node_auth.settings', None)
    def test_get_token_keyword_attribute_error(self):
        """
        test get_token_keyword raises ImproperlyConfigured for attribute error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_token_keyword()




if __name__ == "__main__":
    unittest.main()