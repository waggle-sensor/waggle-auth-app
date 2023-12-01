from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from app.models import Node
from manifests.models import NodeData, LorawanDevice, LorawanConnection
from manifests.serializers import LorawanConnectionSerializer
from manifests.views import LorawanConnectionView
from node_auth.authentication import TokenAuthentication
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework.permissions import AllowAny

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
    
    def tearDown(self):
        NodeData.objects.all().delete()
        LorawanDevice.objects.all().delete()
        LorawanConnection.objects.all().delete()

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_retrieve_existing_lorawan_connection(self):
        """Test lorawan connection view for retrieving records happy path"""
        # Create a LorawanConnection for testing
        LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)

        # Create a request to retrieve the LorawanConnection
        url = f"/lorawanconnections/{self.nodedata.vsn}/{self.device.deveui}/"
        request = self.factory.get(url)

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = LorawanConnectionSerializer(LorawanConnection.objects.get()).data
        self.assertEqual(response.data, expected_data)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_retrieve_nonexistent_lorawan_connection(self):
        """Test lorawan connection view for retrieving records sad path"""
        # Attempt to retrieve a nonexistent LorawanConnection
        url = f"/lorawanconnections/nonexistent_vsn/nonexistent_deveui/"
        request = self.factory.get(url)

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn="nonexistent_vsn", lorawan_deveui="nonexistent_deveui")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_create_lorawan_connection_success(self):
        """Test correctly creating a lorawan connection"""
        # Create a request to create a LorawanConnection
        url = reverse('manifests:create_lorawan_connection')
        data = {
            "node": self.nodedata.vsn,
            "lorawan_device": self.device.deveui,
            "connection_type": "OTAA"
        }
        request = self.factory.post(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "LorawanConnection created successfully"})

        # Check if the LorawanConnection is created in the database
        lorawan_connection = LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)
        self.assertIsNotNone(lorawan_connection)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_create_lorawan_connection_invalid_node(self):
        """Test creating a lorawan connection with invalid node"""
        # Create a request to create a LorawanConnection with an invalid node
        nonexistent_vsn = 'nonexistent_vsn'
        url = reverse('manifests:create_lorawan_connection')
        data = {
            "node": nonexistent_vsn,
            "lorawan_device": self.device.deveui,
            "connection_type": "OTAA"
        }
        request = self.factory.post(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request)

        # Check the response status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": f"Node with vsn {nonexistent_vsn} does not exist"})

        # Check that no LorawanConnection is created in the database
        with self.assertRaises(LorawanConnection.DoesNotExist):
            LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_create_lorawan_connection_invalid_device(self):
        """Test creating a lorawan connection with invalid device"""
        # Create a request to create a LorawanConnection with an invalid node
        nonexistent_deveui = '121456984'
        url = reverse('manifests:create_lorawan_connection')
        data = {
            "node": self.nodedata.vsn,
            "lorawan_device": nonexistent_deveui,
            "connection_type": "OTAA"
        }
        request = self.factory.post(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request)

        # Check the response status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": f"Lorawan Device with deveui {nonexistent_deveui} does not exist"})

        # Check that no LorawanConnection is created in the database
        with self.assertRaises(LorawanConnection.DoesNotExist):
            LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_create_lorawan_connection_serializer_error(self):
        """Test for getting a serializer error when creating a lorawan connection"""
        # Create a request to create a LorawanConnection
        url = reverse('manifests:create_lorawan_connection')
        data = {
            "node": self.nodedata.vsn,
            "lorawan_device": self.device.deveui,
            "connection_type": "error"
        }
        request = self.factory.post(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_success(self):
        """Test correctly updating a lorawan connection"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        #create request
        url = reverse('manifests:update_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"connection_type": "OTAA"}
        request = self.factory.patch(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "LorawanConnection updated successfully"})

        # Check if the LorawanConnection is updated in the database
        lorawan_connection = LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)
        self.assertEqual(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_invalid_node(self):
        """Test update a lorawan connection with invalid node"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        #create request
        nonexistent_vsn = 'nonexistent_vsn'
        url = reverse('manifests:update_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"node": nonexistent_vsn, "connection_type": "OTAA"}
        request = self.factory.patch(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": f"Node with vsn {nonexistent_vsn} does not exist"})

        # Check if the LorawanConnection is not updated in the database
        lorawan_connection = LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)
        self.assertNotEquals(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_invalid_device(self):
        """Test update a lorawan connection with invalid device"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        #create request
        nonexistent_deveui = 'nonexistent_deveui'
        url = reverse('manifests:update_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"lorawan_device": nonexistent_deveui, "connection_type": "OTAA"}
        request = self.factory.patch(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": f"Lorawan Device with deveui {nonexistent_deveui} does not exist"})

        # Check if the LorawanConnection is not updated in the database
        lorawan_connection = LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)
        self.assertNotEquals(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_serializer_error(self):
        """Test for getting a serializer error when updating a lorawan connection"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        # Create a request to create a LorawanConnection
        url = reverse('manifests:update_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"connection_type": "error"}
        request = self.factory.patch(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
