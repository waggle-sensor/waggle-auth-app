from django.test import TestCase
from .models import *


class ManifestInitialTest(TestCase):
    def setUp(self):
        self.Node = NodeData.objects.create(
            vsn="A", name="A_name", gps_lat=50.00, gps_lon=50.00
        )

        tag1 = Tag.objects.create(tag="t1")
        self.Node.tags.set([tag1.pk])

        compute1 = ComputeHardware.objects.create(hardware="h1")
        self.Node.computes.set([compute1.pk])

    def test_node_creation(self):
        N = self.Node
        self.assertTrue(isinstance(N, NodeData))

    def test_node_has_a_tag(self):
        N = self.Node
        self.assertEqual(N.tags.count(), 1)

    def test_node_has_a_compute(self):
        N = self.Node
        self.assertEqual(N.computes.count(), 1)


class ManifestTest(TestCase):
    def test_get_manifest(self):
        self.createComputeHardware(
            [
                {"hardware": "nx1", "hw_model": "Nvidia Jetson Xavier"},
                {"hardware": "rpi4", "hw_model": "Raspberry PI 4"},
            ]
        )

        self.createSensorHardware(
            [
                {"hardware": "bme280", "hw_model": "BME280"},
                {"hardware": "bme680", "hw_model": "BME680"},
            ]
        )

        self.createManifests(
            [
                {
                    "vsn": "W123",
                    "gps_lat": 41.881832,
                    "gps_lon": -87.623177,
                    "computes": [
                        {
                            "name": "nxcore",
                            "hardware": "nx1",
                            "sensors": ["bme280"],
                            "zone": "core",
                        },
                        {
                            "name": "nxagent",
                            "hardware": "nx1",
                            "sensors": [],
                            "zone": "agent",
                        },
                        {
                            "name": "rpi",
                            "hardware": "rpi4",
                            "sensors": ["bme680"],
                            "zone": "shield",
                        },
                    ],
                },
            ]
        )

        # TODO(sean) move to own check
        r = self.client.get("/manifests/")
        self.assertEqual(r.status_code, 200)
        manifests = r.json()
        self.assertEqual(len(manifests), 1)

        r = self.client.get("/manifests/W123/")
        self.assertEqual(r.status_code, 200)
        manifest = r.json()

        self.assertManifestContainsSubset(
            manifest,
            {
                "vsn": "W123",
                "gps_lat": 41.881832,
                "gps_lon": -87.623177,
                "computes": [
                    {
                        "name": "nxcore",
                        "hardware": {
                            "hardware": "nx1",
                            "hw_model": "Nvidia Jetson Xavier",
                        },
                    },
                    {
                        "name": "nxagent",
                        "hardware": {
                            "hardware": "nx1",
                            "hw_model": "Nvidia Jetson Xavier",
                        },
                    },
                    {
                        "name": "rpi",
                        "hardware": {
                            "hardware": "rpi4",
                            "hw_model": "Raspberry PI 4",
                        },
                    },
                ],
            },
        )

    def createComputeHardware(self, hardware):
        """
        Helper function which populates compute hardware test data.
        """
        for item in hardware:
            ComputeHardware.objects.create(
                hardware=item["hardware"], hw_model=item["hw_model"]
            )

    def createSensorHardware(self, hardware):
        """
        Helper function which populates sensor hardware test data.
        """
        for item in hardware:
            SensorHardware.objects.create(
                hardware=item["hardware"], hw_model=item["hw_model"]
            )

    def createManifests(self, manifests):
        """
        Helper function which populates manifest test data.
        """
        for manifest in manifests:
            node_obj = NodeData.objects.create(
                vsn=manifest["vsn"],
                gps_lat=manifest["gps_lat"],
                gps_lon=manifest["gps_lon"],
            )
            for compute in manifest["computes"]:
                compute_obj = Compute.objects.create(
                    node=node_obj,
                    hardware=ComputeHardware.objects.get(hardware=compute["hardware"]),
                    name=compute["name"],
                )
                for sensor in compute["sensors"]:
                    ComputeSensor.objects.create(
                        hardware=SensorHardware.objects.get(hardware=sensor),
                        scope=compute_obj,
                    )

    def assertManifestContainsSubset(self, item, expect):
        """
        Helper function which checks that expect is a "submanifest" of item.

        NOTE(sean) Unlike the built-in assertDictContainsSubset, this function
        recursively asserts child fields are equal.

        TODO(sean) I would personally like to keep test code as simple as possible
        and this is borderline too complicated. We should see if we can change
        how we're checking all this later.
        """
        if isinstance(expect, dict):
            self.assertIsInstance(item, dict)
            for k, v in expect.items():
                self.assertIn(k, item)
                self.assertManifestContainsSubset(item[k], v)
        elif isinstance(expect, list):
            self.assertIsInstance(item, list)
            self.assertEqual(len(item), len(expect))
            for a, b in zip(item, expect):
                self.assertManifestContainsSubset(a, b)
        elif isinstance(expect, float):
            self.assertAlmostEqual(item, expect)
        else:
            self.assertEqual(item, expect)


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
        self.assertCountEqual(
            [item["vsns"] for item in items], [[],[]]
        )

        # assign sensors to nodes under different projects
        project_a = NodeBuildProject.objects.create(name="ProjA")
        project_b = NodeBuildProject.objects.create(name="ProjB")
        node_a = NodeData.objects.create(vsn="A123", name="A_name", project=project_a, phase='Deployed')
        node_b = NodeData.objects.create(vsn="B123", name="B_name", project=project_b, phase='Awaiting Shipment')
        sensor_a = SensorHardware.objects.create(hardware="top_camera", hw_model="fe-8010")
        sensor_b = SensorHardware.objects.create(hardware="bottom_camera", hw_model="ptz-8081")
        sensor_c = SensorHardware.objects.create(hardware="lorawan_temp", hw_model="temp")
        ld = LorawanDevice.objects.create(deveui="234",hardware=sensor_c,name="test")
        NodeSensor.objects.create(node=node_a, hardware=sensor_a)
        NodeSensor.objects.create(node=node_b, hardware=sensor_a)
        NodeSensor.objects.create(node=node_b, hardware=sensor_b)
        LorawanConnection.objects.create(node=node_a,connection_type="OTAA",lorawan_device=ld)

        # request without filters
        r = self.client.get("/sensors/")
        self.assertEqual(r.status_code, 200)
        items = r.json()

        # check for top_camera
        sensors = list(filter(lambda o: o["hardware"] == "top_camera", items))
        self.assertEqual(len(sensors), 1)
        vsns = sensors[0]["vsns"]
        self.assertCountEqual(vsns, ['A123', 'B123'])

        # check for bottom_camera
        sensors = list(filter(lambda o: o["hardware"] == "bottom_camera", items))
        self.assertEqual(len(sensors), 1)
        vsns = sensors[0]["vsns"]
        self.assertCountEqual(vsns, ['B123'])

        # check for lorawan temp sensor
        sensors = list(filter(lambda o: o["hardware"] == "lorawan_temp", items))
        self.assertEqual(len(sensors), 1)
        vsns = sensors[0]["vsns"]
        self.assertCountEqual(vsns, ['A123'])

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
        self.assertCountEqual(sensors[0]["vsns"], ['B123'])

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


class NodeBuildsTest(TestCase):
    def test_list(self):
        project = NodeBuildProject.objects.create(name="Test")
        NodeBuild.objects.create(vsn="W001", shield=True, modem=False)
        NodeBuild.objects.create(vsn="W002", agent=True, project=project)

        r = self.client.get("/node-builds/")
        self.assertEqual(r.status_code, 200)
        items = r.json()

        self.assertDictContainsSubset(
            {
                "vsn": "W001",
                "project": None,
                "top_camera": None,
                "bottom_camera": None,
                "left_camera": None,
                "right_camera": None,
                "agent": False,
                "shield": True,
                "modem": False,
                "modem_sim_type": None,
            },
            items[0],
        )

        self.assertDictContainsSubset(
            {
                "vsn": "W002",
                "project": "Test",
                "top_camera": None,
                "bottom_camera": None,
                "left_camera": None,
                "right_camera": None,
                "agent": True,
                "shield": False,
                "modem": False,
                "modem_sim_type": None,
            },
            items[1],
        )
