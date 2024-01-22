from django.test import TestCase
from rest_framework.test import APIRequestFactory
from app.models import Node
from node_auth.serializers import AuthTokenSerializer
from rest_framework import serializers
from node_auth import get_node_model

Node = get_node_model()

class TestAuthTokenSerializer(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def tearDown(self):
        Node.objects.all().delete()

    def test_validate_valid_node(self):
        """
        Test that validate method returns attrs with vsn as a Node instance for a valid node.
        """
        # Create a test node
        node = Node.objects.create(vsn="W001")

        # Create a serializer instance with vsn from the test node
        data = {"node": "W001", "key": "sample_key"}
        serializer = AuthTokenSerializer(data=data)

        # Validate the serializer
        serializer.is_valid()
        print(serializer.errors)
        self.assertTrue(serializer.is_valid())
        attrs = serializer.validated_data

        # Assertions
        self.assertIn("node", attrs)
        self.assertEqual(attrs["node"]['vsn'], 'W001')

    def test_validate_invalid_node(self):
        """
        Test that validate method raises a ValidationError for an invalid node.
        """
        # Create a serializer instance with vsn for a non-existent node
        data = {"node": "InvalidVSN", "key": "sample_key"}
        serializer = AuthTokenSerializer(data=data)

        # Validate the serializer
        with self.assertRaisesMessage(serializers.ValidationError, "Node not registered"):
            serializer.is_valid(raise_exception=True)

if __name__ == "__main__":
    unittest.main()
