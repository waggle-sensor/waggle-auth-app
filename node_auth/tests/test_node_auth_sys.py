from django.test import TestCase, RequestFactory
from manifests.models import NodeData, LorawanDevice
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
from node_auth.authentication import TokenAuthentication
from node_auth import get_token_keyword, get_token_model, get_node_model
from unittest.mock import patch, Mock

Token = get_token_model()
Node = get_node_model()

class NodeTokenAuthTests(TestCase):
    """
    Node Token Authentication Test. if any of the test fail:
        - Nodes have access to actions/records it shouldn't 
        - Or nodes don't have access to actions/records it should
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.Myvsn = 'W001'
        self.mac = '111'
        self.node = Node.objects.create(vsn=self.Myvsn, mac=self.mac)
        self.token = Token.objects.get(node=self.node)
        self.key = self.token.key
        self.nodedata = NodeData.objects.create(vsn=self.Myvsn)
        self.NotMy_vsn = 'W002'
        self.NotMy_mac = '222'
        self.NotMy_node = Node.objects.create(vsn=self.NotMy_vsn, mac=self.NotMy_mac)
        self.NotMy_token = Token.objects.get(node=self.NotMy_node)
        self.NotMy_key = self.NotMy_token.key
        self.NotMy_nodedata = NodeData.objects.create(vsn=self.NotMy_vsn)
        self.auth_header = get_token_keyword() + " " + self.key
        self.wrong_auth_header = get_token_keyword() + " 123"

    def tearDown(self):
        Node.objects.all().delete()
        Token.objects.all().delete()
        NodeData.objects.all().delete()

    def test_correct_token(self):
        """
        Test node token authentication using correct token
        """

        request = self.factory.post("/", HTTP_AUTHORIZATION=self.auth_header)
        request.node = Mock() #I have to create mock since it doesn't pass through node_auth middleware
        request.node.vsn = self.Myvsn

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
        request = self.factory.post("/", HTTP_AUTHORIZATION=self.wrong_auth_header)
        request.node = Mock()
        request.node.vsn = self.NotMy_vsn

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

        request = self.factory.get("/", HTTP_AUTHORIZATION=self.auth_header)
        request.node = Mock()
        request.node.vsn = self.Myvsn

        # Create a simple view with the permission
        class TestView(NodeOwnedObjectsMixin, RetrieveAPIView):
            serializer_class = ManifestSerializer
            queryset = NodeData.objects.all()
            lookup_field = "vsn"

        # Set the request attribute on the view using the existing response
        view = TestView.as_view()
        response = view(request,vsn=self.Myvsn)

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Expected status code 200")
        

    def test_wrong_objectlevel_auth(self):
        """
        Test object level node authentication using wrong token
        """

        request = self.factory.get("/", HTTP_AUTHORIZATION=self.wrong_auth_header)
        request.node = Mock()
        request.node.vsn = self.NotMy_vsn

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

        request = self.factory.get("/", HTTP_AUTHORIZATION=self.auth_header)
        request.node = Mock()
        request.node.vsn = self.Myvsn

        # Create a simple view with the permission
        class TestView(NodeOwnedObjectsMixin, ReadOnlyModelViewSet, APIView):
            serializer_class = ManifestSerializer
            queryset = NodeData.objects.all()
            lookup_field = "vsn"

        # Set the request attribute on the view using the existing response
        view = TestView.as_view({'get': 'list'})
        response = view(request,pk=self.Myvsn)

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
        url = reverse('manifests:C_lorawan_connection')
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
        url = reverse('manifests:C_lorawan_connection')
        response = self.csrf_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "Expected status code 403, Forbidden")

if __name__ == "__main__":
    unittest.main()