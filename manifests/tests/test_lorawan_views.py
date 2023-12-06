from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from manifests.models import NodeData, LorawanDevice, LorawanConnection, LorawanKeys
from manifests.serializers import LorawanConnectionSerializer, LorawanKeysSerializer, LorawanDeviceSerializer
from manifests.views import LorawanConnectionView, LorawanKeysView, LorawanDeviceView
from node_auth.authentication import TokenAuthentication
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework.permissions import AllowAny
from node_auth import get_token_keyword, get_token_model, get_node_model

HEADER_PREFIX =  get_token_keyword() + ' '
Token = get_token_model()
Node = get_node_model()

class LorawanConnectionViewTestCase(TestCase):
    def setUp(self):
        # Create necessary objects for testing
        self.Myvsn = 'W001'
        self.mac = '111'
        self.deveui = '123456789'
        self.device_name = "test"
        self.factory = APIRequestFactory()
        self.node = Node.objects.create(vsn=self.Myvsn, mac=self.mac)
        self.token = Token.objects.get(node=self.node)
        self.key = self.token.key
        self.nodedata = NodeData.objects.create(vsn=self.Myvsn)  
        self.device = LorawanDevice.objects.create(deveui=self.deveui, device_name= self.device_name)
    
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
        url = reverse('manifests:retrieve_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
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
        url = reverse('manifests:retrieve_lorawan_connection',kwargs={'node_vsn': "nonexistent_vsn",'lorawan_deveui': "nonexistent_deveui"})
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

        # Check that no LorawanConnection is not created in the database
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

        # Check that no LorawanConnection is not created in the database
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

        # Check that no LorawanConnection is not created in the database
        with self.assertRaises(LorawanConnection.DoesNotExist):
            LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_success(self):
        """Test correctly updating a lorawan connection"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        #request
        url = reverse('manifests:update_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"connection_type": "OTAA"}
        request = self.factory.patch(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the LorawanConnection is updated in the database
        lorawan_connection = LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)
        self.assertEqual(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_invalid_node(self):
        """Test update a lorawan connection with invalid node"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        #request
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
        self.assertNotEqual(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_invalid_device(self):
        """Test update a lorawan connection with invalid device"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        #request
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
        self.assertNotEqual(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanConnectionView.permission_classes', [AllowAny])
    def test_update_lorawan_connection_serializer_error(self):
        """Test for getting a serializer error when updating a lorawan connection"""
        # Create a LorawanConnection
        lorawan_connection = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device, connection_type="ABP")

        # Create a request to update a LorawanConnection
        url = reverse('manifests:update_lorawan_connection',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"connection_type": "error"}
        request = self.factory.patch(url, data, format="json")

        # Use the LorawanConnectionView to handle the request
        lorawan_connection_view = LorawanConnectionView.as_view()
        response = lorawan_connection_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check if the LorawanConnection is not updated in the database
        lorawan_connection = LorawanConnection.objects.get(node=self.nodedata, lorawan_device=self.device)
        self.assertNotEqual(lorawan_connection.connection_type, data["connection_type"])

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_retrieve_existing_lorawan_key(self):
        """Test lorawan key view for retrieving records happy path"""
        # Create a LorawanConnection and key for testing
        lc = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)
        LorawanKeys.objects.create(lorawan_connection= lc, network_Key= '123', app_session_key= '13', dev_address='14')

        # Create a request to retrieve the keys
        url = reverse('manifests:retrieve_lorawan_key',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        request = self.factory.get(url)

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = LorawanKeysSerializer(LorawanKeys.objects.get()).data
        self.assertEqual(response.data, expected_data)

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_retrieve_nonexistent_lorawan_key(self):
        """Test lorawan key view for retrieving records sad path"""
        # Attempt to retrieve a nonexistent key
        url = reverse('manifests:retrieve_lorawan_key',kwargs={'node_vsn': "nonexistent_vsn",'lorawan_deveui': "nonexistent_deveui"})
        request = self.factory.get(url)

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request, node_vsn="nonexistent_vsn", lorawan_deveui="nonexistent_deveui")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_create_lorawan_key_success(self):
        """Test correctly creating a lorawan key"""
        # Create a LorawanConnection for testing
        lc = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)

        # Create a request to create a key
        url = reverse('manifests:create_lorawan_key')
        data = {
            "lorawan_connection": str(lc),
            "network_Key": '123',
            "app_session_key": '13',
            "dev_address": '14'
        }
        request = self.factory.post(url, data, format="json")

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the key is created in the database
        lorawan_connection = LorawanKeys.objects.get(lorawan_connection=lc)
        self.assertIsNotNone(lorawan_connection)

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_create_lorawan_key_invalid_lc(self):
        """Test creating a lorawan key with invalid node"""
        # Create a request to create a key with an invalid lc
        nonexistent_lc = 'error-error-error'
        url = reverse('manifests:create_lorawan_key')
        data = {
            "lorawan_connection": nonexistent_lc,
            "network_Key": '123',
            "app_session_key": '13',
            "dev_address": '14'
        }
        request = self.factory.post(url, data, format="json")

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request)

        # Check the response status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": f"Lorawan Connection does not exist"})

        # Check that no key is not created in the database
        with self.assertRaises(LorawanKeys.DoesNotExist):
            LorawanKeys.objects.get(network_Key='123')

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_create_lorawan_key_serializer_error(self):
        """Test for getting a serializer error when creating a lorawan key"""
        # Create a request to create a key
        url = reverse('manifests:create_lorawan_key')
        data = {
            "lorawan_connection": '123',
            "network_Key": '123',
            "app_session_key": '13',
            "dev_address": '14'
        }
        request = self.factory.post(url, data, format="json")

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that key is not created in the database
        with self.assertRaises(LorawanKeys.DoesNotExist):
            LorawanKeys.objects.get(network_Key=123)

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_update_lorawan_key_success(self):
        """Test correctly updating a lorawan key"""
        # Create a LorawanConnection and key for testing
        lc = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)
        LorawanKeys.objects.create(lorawan_connection= lc, network_Key= '123', app_session_key= '13', dev_address= '14')

        #request
        url = reverse('manifests:update_lorawan_key',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"network_Key": '111'}
        request = self.factory.patch(url, data, format="json")

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the key is updated in the database
        key = LorawanKeys.objects.get(lorawan_connection=lc)
        self.assertEqual(key.network_Key, data["network_Key"])

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_update_lorawan_key_invalid_lc(self):
        """Test creating a lorawan key with invalid node"""
        # Create a LorawanConnection and key for testing
        lc = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)
        LorawanKeys.objects.create(lorawan_connection= lc, network_Key= '123', app_session_key= '13', dev_address= '14')

        # Create a request to create a key with an invalid lc
        nonexistent_lc = 'error-error-error'
        url = reverse('manifests:update_lorawan_key',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"lorawan_connection": nonexistent_lc, "network_Key": '111'}
        request = self.factory.patch(url, data, format="json")

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        # Check the response status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"message": f"Lorawan Connection does not exist"})

        # Check if the key is not updated in the database
        key = LorawanKeys.objects.get(lorawan_connection= lc)
        self.assertNotEqual(key.network_Key, data["network_Key"])

    @patch('manifests.views.LorawanKeysView.permission_classes', [AllowAny])
    def test_update_lorawan_key_serializer_error(self):
        """Test for getting a serializer error when updating a lorawan key"""
        # Create a LorawanConnection and key for testing
        lc = LorawanConnection.objects.create(node=self.nodedata, lorawan_device=self.device)
        LorawanKeys.objects.create(lorawan_connection= lc, network_Key= '123', app_session_key= '13', dev_address= '14')

        #request
        url = reverse('manifests:update_lorawan_key',kwargs={'node_vsn': self.nodedata.vsn,'lorawan_deveui': self.device.deveui})
        data = {"dev_address": '123456789', "app_session_key": '222'}
        request = self.factory.patch(url, data, format="json")

        # Use the key view to handle the request
        lorawan_key_view = LorawanKeysView.as_view()
        response = lorawan_key_view(request, node_vsn=self.nodedata.vsn, lorawan_deveui=self.device.deveui)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that key is not created in the database
        with self.assertRaises(LorawanKeys.DoesNotExist):
            LorawanKeys.objects.get(app_session_key='222')

    @patch('manifests.views.LorawanDeviceView.permission_classes', [AllowAny])
    def test_retrieve_existing_lorawan_device(self):
        """Test lorawan device view for retrieving records happy path"""
        # Create a request to retrieve the device
        url = reverse('manifests:lorawandevices-detail',kwargs={'deveui': self.device.deveui})
        request = self.factory.get(url)

        # Use the LorawanDeviceView to handle the request
        lorawan_device_view = LorawanDeviceView.as_view({'get': 'retrieve'})
        response = lorawan_device_view(request, deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = LorawanDeviceSerializer(LorawanDevice.objects.get()).data
        self.assertEqual(response.data, expected_data)

    @patch('manifests.views.LorawanDeviceView.permission_classes', [AllowAny])
    def test_retrieve_nonexistent_lorawan_device(self):
        """Test lorawan device view for retrieving records sad path"""
        # Attempt to retrieve a nonexistent device
        url = reverse('manifests:lorawandevices-detail',kwargs={'deveui': "nonexistent_deveui"})
        request = self.factory.get(url)

        # Use the device view to handle the request
        lorawan_device_view = LorawanDeviceView.as_view({'get': 'retrieve'})
        response = lorawan_device_view(request, deveui="nonexistent_deveui")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('manifests.views.LorawanDeviceView.permission_classes', [AllowAny])
    def test_create_lorawan_device_success(self):
        """Test correctly creating a lorawan device"""
        # Create a request to create a device
        deveui = "451"
        url = reverse('manifests:lorawandevices-list')
        data = {
            "deveui": deveui,
            "device_name": "test",
        }
        request = self.factory.post(url, data, format="json")

        # Use the device view to handle the request
        lorawan_device_view = LorawanDeviceView.as_view({'post': 'create'})
        response = lorawan_device_view(request)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the device is created in the database
        device = LorawanDevice.objects.get(deveui=deveui)
        self.assertIsNotNone(device)

    @patch('manifests.views.LorawanDeviceView.permission_classes', [AllowAny])
    def test_create_lorawan_device_serializer_error(self):
        """Test for getting a serializer error when creating a lorawan device"""
        # Create a request to create a device
        deveui = "123456789123456789"
        url = reverse('manifests:lorawandevices-list')
        data = {
            "deveui": deveui,
            "device_name": "test",
        }
        request = self.factory.post(url, data, format="json")

        # Use the device view to handle the request
        lorawan_device_view = LorawanDeviceView.as_view({'post': 'create'})
        response = lorawan_device_view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that device is not created in the database
        with self.assertRaises(LorawanDevice.DoesNotExist):
            LorawanDevice.objects.get(deveui=deveui)

    @patch('manifests.views.LorawanDeviceView.permission_classes', [AllowAny])
    def test_update_lorawan_device_success(self):
        """Test correctly updating a lorawan device"""
        #request
        url = reverse('manifests:lorawandevices-detail',kwargs={'deveui': self.device.deveui})
        data = {"battery_level": 2.1}
        request = self.factory.patch(url, data, format="json")

        # Use the device view to handle the request
        lorawan_device_view = LorawanDeviceView.as_view({'patch': 'partial_update'})
        response = lorawan_device_view(request, deveui=self.device.deveui)

        # Check the response status code and data
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the device is updated in the database
        device = LorawanDevice.objects.get(deveui= self.device.deveui)
        self.assertEqual(float(device.battery_level), data["battery_level"])

    @patch('manifests.views.LorawanDeviceView.permission_classes', [AllowAny])
    def test_update_lorawan_device_serializer_error(self):
        """Test for getting a serializer error when updating a lorawan device"""
        # Create a request to update a device
        url = reverse('manifests:lorawandevices-detail',kwargs={'deveui': self.device.deveui})
        data = {"deveui": "123456789123456789", "device_name": "update"}
        request = self.factory.patch(url, data, format="json")

        # Use the device view to handle the request
        lorawan_device_view = LorawanDeviceView.as_view({'patch': 'partial_update'})
        response = lorawan_device_view(request, deveui=self.device.deveui)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that device is not updated in the database
        device = LorawanDevice.objects.get(deveui=self.device.deveui)
        self.assertNotEqual(device.device_name, data["device_name"])