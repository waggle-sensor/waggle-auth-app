from django.test import TestCase, RequestFactory
from manifests.models import NodeData
from rest_framework.views import APIView
import unittest
from unittest.mock import patch, Mock
from node_auth.permissions import IsAuthenticated, IsAuthenticated_ObjectLevel, OnlyCreateToSelf
from rest_framework import exceptions
from node_auth import get_node_token_model

Token = get_node_token_model()

class TestIsAuthenticatedPermission(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_has_permission_authenticated_node(self):
        """
        Test that has_permission returns node and its vsn.
        """
        Myvsn = 'W030'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the IsAuthenticated permission
        permission = IsAuthenticated()

        # Check if the permission allows access
        result = permission.has_permission(request, APIView())

        self.assertTrue(result)

    def test_has_permission_exception_handling_nonode(self):
        """ Test that has_permission raise error when request has no node """
        # Create a mock request with a node that triggers an exception
        request = self.factory.get('/')

        # Create an instance of the IsAuthenticated permission
        permission = IsAuthenticated()

        with self.assertRaises(exceptions.AuthenticationFailed) as context:
            permission.has_permission(request, APIView())

class MockedObjectModel:
    """
    Mocked model with optional nested attributes.
    """
    def __init__(self, related_object=None, IsLayerOne = False):
        self.related_object = related_object or Mock()
        self.node = Mock() if IsLayerOne else None

class TestIsAuthenticatedObjectLevelPermission(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_call_method(self):
        """ Test calling IsAuthenticated_ObjectLevel() as if it were a function"""
        permission = IsAuthenticated_ObjectLevel()

        # Call the __call__ method
        result = permission()

        self.assertEqual(result, permission)

    def test_has_object_permission_matching_vsn(self):
        """ Test that has_object_permission returns True for an object with matching vsn."""
        Myvsn = 'W030'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the IsAuthenticated_ObjectLevel permission
        permission = IsAuthenticated_ObjectLevel()

        # Create an object with a vsn matching the authenticated node's vsn
        obj = NodeData(vsn=Myvsn)

        # Check if the permission allows access to the object
        result = permission.has_object_permission(request, APIView(), obj)

        self.assertTrue(result)

    def test_has_object_permission_not_matching_vsn(self):
        """ Test that has_object_permission returns False for an object with a non-matching vsn. """
        Myvsn = 'W030'
        Not_Myvsn = 'W031'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the IsAuthenticated_ObjectLevel permission
        permission = IsAuthenticated_ObjectLevel()

        # Create an object with a vsn not matching the authenticated node's vsn
        obj = NodeData(vsn=Not_Myvsn)

        # Check if the permission allows access to the object
        result = permission.has_object_permission(request, APIView(), obj)

        self.assertFalse(result)

    def test_has_object_permission_multiple_attributes_matching_vsn(self):
        """
        Test that has_object_permission returns True for an object with matching vsn (nested attributes to get node table).
        """
        Myvsn = 'W030'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the IsAuthenticated_ObjectLevel permission
        permission = IsAuthenticated_ObjectLevel()

        # Create a mock instance of the lightweight MockedObjectModel
        obj = MockedObjectModel()

        # Set the vsn attribute to match the authenticated node's vsn
        obj.related_object.nested_attribute.node.vsn = Myvsn

        # Set the foreign key name on the view
        view = APIView()
        view.foreign_key_name = 'related_object__nested_attribute__node'

        # Check if the permission allows access to the object
        result = permission.has_object_permission(request, view, obj)

        self.assertTrue(result)

    def test_has_object_permission_multiple_attributes_not_matching_vsn(self):
        """
        Test that has_object_permission returns False for an object with a non-matching vsn (nested attributes to get node table).
        """
        Myvsn = 'W030'
        Not_Myvsn = 'W031'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the IsAuthenticated_ObjectLevel permission
        permission = IsAuthenticated_ObjectLevel()

        # Create a mock instance of the lightweight MockedObjectModel
        obj = MockedObjectModel()

        # Set the vsn attribute to match the authenticated node's vsn
        obj.related_object.nested_attribute.node.vsn = Not_Myvsn

        # Set the foreign key name on the view
        view = APIView()
        view.foreign_key_name = 'related_object__nested_attribute__node'

        # Check if the permission allows access to the object
        result = permission.has_object_permission(request, view, obj)

        self.assertFalse(result)


    def test_has_object_permission_multiple_attributes_AttributeError(self):
        """
        Test that has_object_permission raises AttributeError for an object that states its related to a model
        in foreign_key_name but it is not (nested relationships to get node table).
        """
        Myvsn = 'W030'

        # Create a mock request
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the IsAuthenticated_ObjectLevel permission
        permission = IsAuthenticated_ObjectLevel()

        # Create a mock instance of the nested relationships
        obj = MockedObjectModel(IsLayerOne=True)
        obj.node.vsn = Myvsn
        obj_2 = MockedObjectModel(related_object=obj)
        obj_3 = MockedObjectModel(related_object=obj_2)

        # Set the foreign key name on the view
        view = APIView()
        view.foreign_key_name = 'related_object__test__node'

        with self.assertRaises(exceptions.ParseError) as context:
            permission.has_object_permission(request, view, obj_3)

class TestOnlyCreateToSelfPermission(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_call_method(self):
        """ Test calling OnlyCreateToSelf() as if it were a function"""
        permission = OnlyCreateToSelf()

        # Call the __call__ method
        result = permission()

        self.assertEqual(result, permission)

    def test_has_permission_post_request_associated_to_self(self):
        """ Test that has_permission returns True for a POST request associated to self. """
        Myvsn = 'W030'

        # Create a mock request with an authenticated node and POST method
        request = self.factory.post('/')
        request.node = Mock()
        request.node.vsn = Myvsn
        data = {'node': Myvsn}
        request.data = data

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        # Set view
        view = APIView()

        # Check if the permission allows access
        result = permission.has_permission(request, view)

        self.assertTrue(result)

    def test_has_permission_post_request_not_associated_to_self(self):
        """ Test that has_permission returns False for a POST request not associated to self. """
        Myvsn = 'W030'
        Not_Myvsn = 'W031'

        # Create a mock request with an authenticated node and POST method
        request = self.factory.post('/')
        request.node = Mock()
        request.node.vsn = Myvsn
        data = {'node': Not_Myvsn}
        request.data = data

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        # Set view
        view = APIView()

        # Check if the permission allows access
        result = permission.has_permission(request, view)

        self.assertFalse(result)

    def test_has_permission_post_request_associated_to_self_using_vsngetfunc(self):
        """
        Test that has_permission returns True for a POST request associated to self using vsngetfunc().
        """
        Myvsn = 'W030'

        # Create a mock request with an authenticated node and POST method
        request = self.factory.post('/')
        request.node = Mock()
        request.node.vsn = Myvsn
        data = {'node': Myvsn}
        request.data = data

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        # Set view
        view = APIView()

        # Mock vsn_get_func to return vsn associated with the request data
        view.vsn_get_func = lambda _, req, fk_name: req.data.get(fk_name)

        # Check if the permission allows access
        result = permission.has_permission(request, view)

        self.assertTrue(result)

    def test_has_permission_post_request_associated_to_self_using_foreignkeyname(self):
        """
        Test that has_permission returns False for a POST request associated to self using foreignkeyname.
        """
        Myvsn = 'W030'
        Not_Myvsn = 'W031'

        # Create a mock request with an authenticated node and POST method
        request = self.factory.post('/')
        request.node = Mock()
        request.node.vsn = Myvsn
        data = {'test': Not_Myvsn}
        request.data = data

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        # Set the foreign key name on the view
        view = APIView()
        view.foreign_key_name = 'test'

        # Check if the permission allows access
        result = permission.has_permission(request, view)

        self.assertFalse(result)

    def test_has_permission_non_post_request(self):
        """
        Test that has_permission returns True for a non-POST request.
        """
        Myvsn = 'W030'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = Mock()
        request.node.vsn = Myvsn

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        # Check if the permission allows access
        result = permission.has_permission(request, APIView())

        self.assertTrue(result)

    def test_has_permission_non_post_request(self):
        """
        Test that has_permission returns False for a non-POST request.
        """
        Myvsn = 'W030'

        # Create a mock request with an authenticated node
        request = self.factory.get('/')
        request.node = None

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        # Check if the permission allows access
        result = permission.has_permission(request, APIView())

        self.assertFalse(result)

    def test_has_permission_exception_handling_nonode(self):
        """ Test that has_permission raise error when request has no node """
        # Create a mock request with a node that triggers an exception
        request = self.factory.get('/')

        # Create an instance of the OnlyCreateToSelf permission
        permission = OnlyCreateToSelf()

        with self.assertRaises(exceptions.AuthenticationFailed) as context:
            permission.has_permission(request, APIView())

if __name__ == "__main__":
    unittest.main()