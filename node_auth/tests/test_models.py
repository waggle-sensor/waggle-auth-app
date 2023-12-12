from django.test import TestCase
from node_auth.models import Token
import unittest
from unittest.mock import patch
from node_auth.models import Token
from node_auth import get_node_token_keyword, get_node_model, get_node_token_model
from django.core.exceptions import ImproperlyConfigured
from node_auth.contrib.auth.models import AnonymousNode

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
    def test_get_node_token_model_ValueError(self):
        """
        test get_node_token_model raises ImproperlyConfigured for value error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_node_token_model()

    @patch('node_auth.settings.AUTH_NODE_TOKEN_MODEL', 'nonexistent_app.NonexistentModel')
    def test_get_node_token_model_lookup_error(self):
        """
        test get_node_token_model raises ImproperlyConfigured for lookup error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_node_token_model()

    @patch('node_auth.settings', None)
    def test_get_node_token_keyword_attribute_error(self):
        """
        test get_node_token_keyword raises ImproperlyConfigured for attribute error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_node_token_keyword()

class AnonymousNodeTestCase(TestCase):

    def test_str_method(self):
        """Test the __str__ method."""
        anonymous_node = AnonymousNode()
        self.assertEqual(str(anonymous_node), "AnonymousNode")

    def test_eq_method(self):
        """Test the __eq__ method."""
        anonymous_node1 = AnonymousNode()
        anonymous_node2 = AnonymousNode()
        self.assertEqual(anonymous_node1, anonymous_node2)

        different_object = object()
        self.assertNotEqual(anonymous_node1, different_object)

    def test_save_method(self):
        """Test the save method."""
        anonymous_node = AnonymousNode()
        with self.assertRaises(NotImplementedError):
            anonymous_node.save()

    def test_delete_method(self):
        """Test the delete method."""
        anonymous_node = AnonymousNode()
        with self.assertRaises(NotImplementedError):
            anonymous_node.delete()

    def test_is_anonymous_property(self):
        """Test the is_anonymous property."""
        anonymous_node = AnonymousNode()
        self.assertTrue(anonymous_node.is_anonymous)

    def test_is_authenticated_property(self):
        """Test the is_authenticated property."""
        anonymous_node = AnonymousNode()
        self.assertFalse(anonymous_node.is_authenticated)

if __name__ == "__main__":
    unittest.main()