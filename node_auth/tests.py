from django.test import TestCase, RequestFactory
from manifests.models import NodeData, LorawanDevice
from app.models import Node
from node_auth.models import Token
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.generics import RetrieveAPIView
from node_auth.mixins import NodeAuthMixin, NodeOwnedObjectsMixin
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpRequest
from manifests.serializers import ManifestSerializer
from django.urls import reverse
import unittest
from unittest.mock import patch
from unittest.mock import Mock
from node_auth.models import Token
from node_auth.permissions import IsAuthenticated, IsAuthenticated_ObjectLevel, OnlyCreateToSelf
from rest_framework import exceptions

class NodeTokenAuthTests(TestCase):
    """
    Node Token Authentication Test. if any of the test fail:
        - Nodes have access to actions/records it shouldn't 
        - Or nodes don't have access to actions/records it should
    """
    model = None
    path = None
    header_prefix = 'node_auth '

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.vsn = 'W001'
        self.mac = '111'
        self.node = Node.objects.create(vsn=self.vsn, mac=self.mac)
        self.token = Token.objects.get(node=self.node)
        self.key = self.token.key
        self.nodedata = NodeData.objects.create(vsn=self.vsn)
        self.NotMy_vsn = 'W002'
        self.NotMy_mac = '222'
        self.NotMy_node = Node.objects.create(vsn=self.NotMy_vsn, mac=self.NotMy_mac)
        self.NotMy_token = Token.objects.get(node=self.NotMy_node)
        self.NotMy_key = self.NotMy_token.key
        self.NotMy_nodedata = NodeData.objects.create(vsn=self.NotMy_vsn)
        self.auth_header = self.header_prefix + self.key
        self.wrong_auth_header = self.header_prefix + "123"

    def test_correct_token(self):
        """
        Test node token authentication using correct token
        """
        request = HttpRequest()
        request.method = 'POST'
        request.path = self.path
        request.META['HTTP_AUTHORIZATION'] = self.auth_header

        # Create a simple view with the permission
        class TestView(NodeAuthMixin, APIView):
            def post(self, request, *args, **kwargs):
                return Response({"status": "success"}, status=status.HTTP_200_OK)

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Expected status code 200")

    def test_wrong_token(self):
        """
        Test node token authentication using wrong token
        """
        request = HttpRequest()
        request.method = 'POST'
        request.path = self.path
        request.META['HTTP_AUTHORIZATION'] = self.wrong_auth_header

        # Create a simple view with the permission
        class TestView(NodeAuthMixin, APIView):
            def post(self, request, *args, **kwargs):
                return Response({"status": "success"}, status=status.HTTP_200_OK)

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Expected status code 401, Unauthorized")

    def test_correct_objectlevel_auth(self):
        """
        Test object level node authentication using correct token
        """

        request = HttpRequest()
        request.method = 'GET'
        request.path = self.path
        request.META['HTTP_AUTHORIZATION'] = self.auth_header

        # Create a simple view with the permission
        class TestView(NodeOwnedObjectsMixin, RetrieveAPIView):
            serializer_class = ManifestSerializer
            queryset = NodeData.objects.all()
            lookup_field = "vsn"

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request,vsn=self.vsn)

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Expected status code 200")
        

    def test_wrong_objectlevel_auth(self):
        """
        Test object level node authentication using wrong token
        """

        request = HttpRequest()
        request.method = 'GET'
        request.path = self.path
        request.META['HTTP_AUTHORIZATION'] = self.auth_header

        # Create a simple view with the permission
        class TestView(NodeOwnedObjectsMixin, RetrieveAPIView):
            serializer_class = ManifestSerializer
            queryset = NodeData.objects.all()
            lookup_field = "vsn"

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request,vsn=self.NotMy_vsn)

        condition = response.status_code == status.HTTP_404_NOT_FOUND or response.status_code ==  status.HTTP_401_UNAUTHORIZED
        self.assertTrue(condition, f"Got status {response.status_code}, expected status code 404 (Object Not Found) or 401 (Unauthorized)")

    def test_objectlevel_auth_list(self):
        """
        Use object level node authentication using correct token to test 
        if list retrieved only includes records related to my node
        """

        request = HttpRequest()
        request.method = 'GET'
        request.path = self.path
        request.META['HTTP_AUTHORIZATION'] = self.auth_header

        # Create a simple view with the permission
        class TestView(NodeOwnedObjectsMixin, ReadOnlyModelViewSet, APIView):
            serializer_class = ManifestSerializer
            queryset = NodeData.objects.all()
            lookup_field = "vsn"

        # Set the request attribute on the view using the existing response
        view = TestView.as_view({'get': 'list'})
        response = view(request,pk=self.vsn)

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Expected status code 200")

        # Check that self.NotMy_vsn is not present in any of the dictionaries in response.data
        not_my_vsn_present = any(data_dict.get('vsn') == self.NotMy_vsn for data_dict in response.data)
        self.assertFalse(not_my_vsn_present, f"Found {self.NotMy_vsn} in the query response. This is not me!")


    def test_correct_OnlyCreateToSelf_auth(self):
        """
        Use object level node authentication using correct token to test 
        if node can create records associated to itself
        """
        device = LorawanDevice.objects.create(deveui="123456789",device_name="test")

        data = {
            "node": self.nodedata.vsn,
            "lorawan_device": device.deveui,
            "connection_type": "OTAA"
        }

        self.csrf_client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        # Use reverse to dynamically generate the URL
        url = reverse('manifests:create_lorawan_connection')
        response = self.csrf_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Expected status code 201, object created")

    def test_wrong_OnlyCreateToSelf_auth(self):
        """
        Use object level node authentication using correct token to test if node 
        cannot create records associated with another node
        """
        device = LorawanDevice.objects.create(deveui="123456789",device_name="test")

        data = {
            "node": self.NotMy_nodedata.vsn,
            "lorawan_device": device.deveui,
            "connection_type": "OTAA"
        }

        self.csrf_client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        # Use reverse to dynamically generate the URL
        url = reverse('manifests:create_lorawan_connection')
        response = self.csrf_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Expected status code 403, Forbidden")

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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = Mock()
        request.user.vsn = Myvsn
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
        request.user = Mock()
        request.user.vsn = Myvsn
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
        request.user = Mock()
        request.user.vsn = Myvsn
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
        request.user = Mock()
        request.user.vsn = Myvsn
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
        request.user = Mock()
        request.user.vsn = Myvsn

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
        request.user = None

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