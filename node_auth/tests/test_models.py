from django.test import TestCase
from node_auth.models import Token
import unittest
from unittest.mock import patch
from node_auth.models import Token

class test_TokenModel(unittest.TestCase):

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
