"""
This file is meant to test manifests/models.py 
"""
from django.test import TestCase
from manifests.models import *
from pytest import mark
from django.core.exceptions import ValidationError

class ModemTestCase(TestCase):

    def setUp(self):
        self.modem = Modem.objects.create(imei="1234567891234579")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.modem), "1234567891234579")

class ComputeHardwareTestCase(TestCase):

    def setUp(self):
        self.computeH = ComputeHardware.objects.create(hardware="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.computeH), "test")

class ResourceHardwareTestCase(TestCase):

    def setUp(self):
        self.resourceH = ResourceHardware.objects.create(hardware="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.resourceH), "test")

class SensorHardwareTestCase(TestCase):

    def setUp(self):
        self.sensorH = SensorHardware.objects.create(hardware="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.sensorH), "test")


class CapabilityTestCase(TestCase):

    def setUp(self):
        self.capability = Capability.objects.create(capability="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.capability), "test")

class ComputeTestCase(TestCase):

    def setUp(self):
        self.node = NodeData.objects.create(vsn="W001")
        self.computeH = ComputeHardware.objects.create(hardware="computeH")
        self.compute = Compute.objects.create(name="test",node=self.node,hardware=self.computeH)

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.compute), "test")

class NodeSensorTestCase(TestCase):

    def setUp(self):
        self.node = NodeData.objects.create(vsn="W001")
        self.sensorH = SensorHardware.objects.create(hardware="sensorH")
        self.sensor = NodeSensor.objects.create(name="test",node=self.node,hardware=self.sensorH)

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.sensor), "test")

class ComputeSensorTestCase(TestCase):

    def setUp(self):
        self.node = NodeData.objects.create(vsn="W001")
        self.computeH = ComputeHardware.objects.create(hardware="computeH")
        self.compute = Compute.objects.create(name="compute",node=self.node,hardware=self.computeH)
        self.sensorH = SensorHardware.objects.create(hardware="sensorH")
        self.sensor = ComputeSensor.objects.create(
            name="sensor",
            hardware=self.sensorH,
            scope=self.compute
        )

    def test_str_method(self):
        """Test the node method."""
        self.assertEqual(self.sensor.node(), self.node)

class TagTestCase(TestCase):

    def setUp(self):
        self.tag = Tag.objects.create(tag="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.tag), "test")

    def test_naturalkey_method(self):
        """Test the natural key method"""
        self.assertEqual(self.tag.natural_key(), "test")

class LabelTestCase(TestCase):

    def setUp(self):
        self.label = Label.objects.create(label="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.label), "test")

    def test_naturalkey_method(self):
        """Test the natural key method"""
        self.assertEqual(self.label.natural_key(), "test")

class NodeBuildProjectTestCase(TestCase):

    def setUp(self):
        self.NBP = NodeBuildProject.objects.create(name="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.NBP), "test")

class NodeBuildTestCase(TestCase):

    def setUp(self):
        self.NB = NodeBuild.objects.create(vsn="test", modem_sim_type="anl-nu")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.NB), "test")
    
    def test_clean_method(self):
        """Test the clean method"""
        # Raises validation error because of modem
        with self.assertRaisesMessage(ValidationError,"{'modem': ['Modem must be set to True if SIM Type is specified.'], 'sim_type': ['SIM Type should be empty if Modem is False.']}"):
            self.NB.clean()

class LorawanDeviceTestCase(TestCase):

    def setUp(self):
        self.ld = LorawanDevice.objects.create(deveui="123", name="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.ld), "test-123")

    def test_naturalkey_method(self):
        """Test the natural key method"""
        self.assertEqual(self.ld.natural_key(), "123")

class LorawanConnectionTestCase(TestCase):

    def setUp(self):
        self.node = NodeData.objects.create(vsn="W001")
        self.ld = LorawanDevice.objects.create(deveui="123", name="test")
        self.lc = LorawanConnection.objects.create(
            node=self.node, 
            lorawan_device=self.ld
        )

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.lc), "W001-test-123")

class LorawanKeysTestCase(TestCase):

    def setUp(self):
        self.node = NodeData.objects.create(vsn="W001")
        self.ld = LorawanDevice.objects.create(deveui="123", name="test")
        self.lc = LorawanConnection.objects.create(
            node=self.node, 
            lorawan_device=self.ld,
            connection_type="OTAA"
        )
        self.lk = LorawanKeys.objects.create(
            lorawan_connection=self.lc,
            network_Key="123",
            app_session_key="13",
            dev_address="14",
        )

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.lk), "W001-test-123")

    def test_clean_method(self):
        """Test the clean method"""
        # Raises validation error because of lorawan connection type
        with self.assertRaisesMessage(ValidationError,"app_key cannot be blank for OTAA connections."):
            self.lk.clean()

class NodeBuildProjectFocusTestCase(TestCase):

    def setUp(self):
        self.NBPF = NodeBuildProjectFocus.objects.create(name="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.NBPF), "test")

class NodeBuildProjectPartnerTestCase(TestCase):

    def setUp(self):
        self.NBPP = NodeBuildProjectPartner.objects.create(name="test")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.NBPP), "test")


class SiteTestCase(TestCase):

    def setUp(self):
        self.site = Site.objects.create(id="ANL")

    def test_str_method(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.site), "ANL")