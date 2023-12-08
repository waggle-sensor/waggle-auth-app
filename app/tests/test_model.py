from django.test import TestCase
import unittest
from unittest.mock import patch
from app.models import Node
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from app import get_user_token_keyword

class NodeTestCases(TestCase):

    def setUp(self):
        self.vsn = "W001"
        self.node = Node.objects.create(vsn=self.vsn)

    def tearDown(self):
        self.node.delete()

    def test_str_method(self):
        """Test the __str__ method"""
        expected_str = self.node.get_vsn()
        self.assertEqual(str(self.node), expected_str)

    def test_get_vsn_method(self):
        """Test the get_vsn method"""
        expected_vsn = self.node.get_vsn()
        self.assertEqual(self.vsn, expected_vsn)

    def test_natural_key_method(self):
        """Test the natural_key method"""
        expected_natural_key = (self.node.get_vsn(),)
        self.assertEqual(self.node.natural_key(), expected_natural_key)

if __name__ == "__main__":
    unittest.main()

class get_functions(TestCase):

    @patch('app.settings', None)
    def test_get_user_token_keyword_attribute_error(self):
        """
        test get_user_token_keyword raises ImproperlyConfigured for attribute error
        """
        with self.assertRaises(ImproperlyConfigured) as context:
            get_user_token_keyword()