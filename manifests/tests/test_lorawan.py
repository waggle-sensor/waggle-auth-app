from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from app.models import Node
from manifests.models import NodeData, LorawanDevice, LorawanConnection
from manifests.serializers import LorawanConnectionSerializer
from manifests.views import LorawanConnectionView
from node_auth.authentication import TokenAuthentication
from unittest.mock import patch, Mock

HEADER_PREFIX =  TokenAuthentication.keyword + ' '

class LorawanConnectionViewTestCase(TestCase):
    def setUp(self):
        # Create necessary objects for testing
        self.Myvsn = 'W001'
        self.mac = '111'
        self.deveui = '123456789'
        self.factory = APIRequestFactory()
        self.node = Node.objects.create(vsn=self.Myvsn, mac=self.mac)
        self.nodedata = NodeData.objects.create(vsn=self.Myvsn)  
        self.device = LorawanDevice.objects.create(deveui=self.deveui)
        self.token = TokenAuthentication.model.objects.get(node=self.node)
        self.key = self.token.key
        self.auth_header = HEADER_PREFIX + self.key
    
    def tearDown(self):
        NodeData.objects.all().delete()
        LorawanDevice.objects.all().delete()
        LorawanConnection.objects.all().delete()

    def test_retrieve_existing_lorawan_connection(self):
        """Test lorawan connection view for retrieving records happy path"""
        # Create a LorawanConnection for testing
        LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)

        # Create a request to retrieve the LorawanConnection
        url = f"/lorawanconnections/{self.nodedata.vsn}/{self.device.deveui}/"
        request = self.factory.get(url, HTTP_AUTHORIZATION=f"{self.auth_header}")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = LorawanConnectionSerializer(LorawanConnection.objects.get()).data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_nonexistent_lorawan_connection(self):
        """Test lorawan connection view for retrieving records sad path"""
        # Attempt to retrieve a nonexistent LorawanConnection
        url = f"/lorawanconnections/nonexistent_vsn/nonexistent_deveui/"
        request = self.factory.get(url, HTTP_AUTHORIZATION=f"{self.auth_header}")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn="nonexistent_vsn", lorawan_deveui="nonexistent_deveui")

        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Add more test methods to cover create and update functionality as needed
