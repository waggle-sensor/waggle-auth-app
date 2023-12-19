from django.test import TestCase
from manifests.models import *
from node_auth import get_node_token_model, get_node_model

Token = get_node_token_model()
Node = get_node_model()

class SensorHardwareViewsTest(TestCase):
    def setUp(self):
        SensorHardware.objects.create(hardware="gps", hw_model="A GPS")
        SensorHardware.objects.create(hardware="raingauge", hw_model="RG-15")

    def test_list_view(self):
        r = self.client.get("/sensors/")
        self.assertEqual(r.status_code, 200)
        items = r.json()
        self.assertCountEqual(
            [item["hardware"] for item in items], ["gps", "raingauge"]
        )

        # vsns should be empty since sensors haven't been assigned to nodes
        self.assertCountEqual([item["vsns"] for item in items], [[], []])

        # assign sensors to nodes under different projects
        project_a = NodeBuildProject.objects.create(name="ProjA")
        project_b = NodeBuildProject.objects.create(name="ProjB")
        node_a = NodeData.objects.create(
            vsn="A123", name="A_name", project=project_a, phase="Deployed"
        )
        node_b = NodeData.objects.create(
            vsn="B123", name="B_name", project=project_b, phase="Awaiting Shipment"
        )
        sensor_a = SensorHardware.objects.create(
            hardware="top_camera", hw_model="fe-8010"
        )
        sensor_b = SensorHardware.objects.create(
            hardware="bottom_camera", hw_model="ptz-8081"
        )
        sensor_c = SensorHardware.objects.create(
            hardware="lorawan_temp", hw_model="temp"
        )
        ld = LorawanDevice.objects.create(deveui="234", hardware=sensor_c, name="test")
        NodeSensor.objects.create(node=node_a, hardware=sensor_a)
        NodeSensor.objects.create(node=node_b, hardware=sensor_a)
        NodeSensor.objects.create(node=node_b, hardware=sensor_b)
        LorawanConnection.objects.create(
            node=node_a, connection_type="OTAA", lorawan_device=ld
        )

        # request without filters
        r = self.client.get("/sensors/")
        self.assertEqual(r.status_code, 200)
        items = r.json()

        # check for top_camera
        sensors = list(filter(lambda o: o["hardware"] == "top_camera", items))
        self.assertEqual(len(sensors), 1)
        vsns = sensors[0]["vsns"]
        self.assertCountEqual(vsns, ["A123", "B123"])

        # check for bottom_camera
        sensors = list(filter(lambda o: o["hardware"] == "bottom_camera", items))
        self.assertEqual(len(sensors), 1)
        vsns = sensors[0]["vsns"]
        self.assertCountEqual(vsns, ["B123"])

        # check for lorawan temp sensor
        sensors = list(filter(lambda o: o["hardware"] == "lorawan_temp", items))
        self.assertEqual(len(sensors), 1)
        vsns = sensors[0]["vsns"]
        self.assertCountEqual(vsns, ["A123"])

        #
        # test requests with filters
        #
        r = self.client.get("/sensors/?project=projA")
        self.assertEqual(r.status_code, 200)
        items = r.json()

        # check 2 sensor is listed (for ProjA)
        self.assertEqual(len(items), 2)
        self.assertCountEqual(items[0]["vsns"], ["A123"])

        # 0 queries
        r = self.client.get("/sensors/?phase=foo")
        self.assertEqual(r.status_code, 200)
        items = r.json()
        self.assertEqual(len(items), 0)

        r = self.client.get("/sensors/?project=foo&phase=Deployed")
        items = r.json()
        self.assertEqual(len(items), 0)

        # good phase
        r = self.client.get("/sensors/?phase=awaiting shipment")
        self.assertEqual(r.status_code, 200)
        items = r.json()
        self.assertEqual(len(items), 2)
        self.assertCountEqual([item["vsns"] for item in items], [["B123"], ["B123"]])

        # multi filtering
        r = self.client.get("/sensors/?phase=deployed,awaiting shipment")
        items = r.json()
        self.assertEqual(len(items), 3)

        sensors = list(filter(lambda o: o["hardware"] == "bottom_camera", items))
        self.assertEqual(len(sensors), 1)
        self.assertCountEqual(sensors[0]["vsns"], ["B123"])

        sensors = list(filter(lambda o: o["hardware"] == "top_camera", items))
        self.assertEqual(len(sensors), 1)
        self.assertCountEqual(sensors[0]["vsns"], ["A123", "B123"])

        r = self.client.get("/sensors/?project=proja&phase=deployed,awaiting shipment")
        items = r.json()
        self.assertEqual(len(items), 2)
        self.assertCountEqual(items[0]["vsns"], ["A123"])

        r = self.client.get("/sensors/?project=proja&phase=awaiting shipment")
        items = r.json()
        self.assertEqual(len(items), 0)

    def test_detail_view(self):
        r = self.client.get("/sensors/gps/")
        self.assertEqual(r.status_code, 200)
        item = r.json()
        self.assertDictContainsSubset(
            {
                "hardware": "gps",
                "hw_model": "A GPS",
            },
            item,
        )

class SensorHardwareNodeCRUDViewSetTest(TestCase):
    def setUp(self):
        self.Myvsn = "W001"
        self.mac = "111"
        self.node = Node.objects.create(vsn=self.Myvsn, mac=self.mac)
        self.token = Token.objects.get(node=self.node)
        self.key = self.token.key
        self.gpsSensor = SensorHardware.objects.create(hardware="gps", hw_model="A GPS")
        self.raingaugeSensor = SensorHardware.objects.create(hardware="raingauge", hw_model="RG-15")

    def test_create(self):
        """Test the Sensor Hardware CREATE endpoint for Authenticated Nodes"""
        data = {"hardware": "test","hw_model": "test-123", "description": "test"}
        r = self.client.post("/sensorhardwares/", data=data, 
            content_type="application/json", HTTP_AUTHORIZATION=f"node_auth {self.key}"
        )
        self.assertEqual(r.status_code, 201)

        #check if the device was created in the db
        sensor_exists = SensorHardware.objects.filter(hw_model=data["hw_model"]).exists()
        self.assertTrue(sensor_exists)

    def test_get(self):
        """Test the Sensor Hardware GET endpoint for Authenticated Nodes"""
        r = self.client.get(f"/sensorhardwares/{self.gpsSensor.hw_model}/", HTTP_AUTHORIZATION=f"node_auth {self.key}")
        self.assertEqual(r.status_code, 200)

        #assert the correct device was returned in the request
        item = r.json()
        self.assertEqual(item["hw_model"], self.gpsSensor.hw_model)

    def test_update(self):
        """Test the Sensor Hardware PATCH endpoint for Authenticated Nodes"""
        data = {"description": "test"}
        r = self.client.patch(f"/sensorhardwares/{self.gpsSensor.hw_model}/",data=data,
            content_type="application/json", HTTP_AUTHORIZATION=f"node_auth {self.key}"
        )
        self.assertEqual(r.status_code, 200)

        # Check if the device was updated in the db
        sensor = SensorHardware.objects.get(pk=self.gpsSensor.pk)
        self.assertEqual(sensor.description, data["description"])

    def test_delete(self):
        """Test the Sensor Hardware DELETE endpoint for Authenticated Nodes"""
        r = self.client.delete(f"/sensorhardwares/{self.gpsSensor.hw_model}/", HTTP_AUTHORIZATION=f"node_auth {self.key}")
        self.assertEqual(r.status_code, 204)

        #check if the device was deleted in the db
        sensor_exists = SensorHardware.objects.filter(hw_model=self.gpsSensor.hw_model).exists()
        self.assertFalse(sensor_exists)

    def test_unauthenticated(self):
        """Test non authenticated request return an error"""
        r = self.client.delete(f"/sensorhardwares/{self.gpsSensor.hw_model}/")
        self.assertEqual(r.status_code, 401)

    def test_wrongToken(self):
        """Test request with wrong token returns an error"""
        r = self.client.get(f"/sensorhardwares/{self.gpsSensor.hw_model}/", HTTP_AUTHORIZATION=f"node_auth wrong_token")
        self.assertEqual(r.status_code, 401)