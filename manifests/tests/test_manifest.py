from django.test import TestCase
from manifests.models import *
from address.models import *
from pytest import mark
from ManifestHelp_fx import *


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
                {"hardware": "lorawan_1", "hw_model": "1"},
                {"hardware": "lorawan_2", "hw_model": "2"},
            ]
        )

        self.createLorawanDevice(
            [
                {"deveui":"123","name":"test","hardware":"lorawan_1"},
                {"deveui":"111","name":"hello","hardware":"lorawan_2"},
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
                    "lorawanconnections": [
                        {
                            "connection_type": "OTAA",
                            "lorawandevice": {
                                "deveui": "123",
                                "hardware": {
                                    "hardware": "lorawan_1",
                                }
                            }
                        },
                        {
                            "connection_type": "OTAA",
                            "lorawandevice": {
                                "deveui": "111",
                                "hardware": {
                                    "hardware": "lorawan_2",
                                },
                            },
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
                "lorawanconnections": [
                    {
                        "connection_type": "OTAA",
                        "lorawandevice": {
                            "deveui": "123",
                            "hardware": {
                                "hardware": "lorawan_1",
                            }
                        }
                    },
                    {
                        "connection_type": "OTAA",
                        "lorawandevice": {
                            "deveui": "111",
                            "hardware": {
                                "hardware": "lorawan_2",
                            },
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
            for lc in manifest["lorawanconnections"]:
                lc_obj = LorawanConnection.objects.create(
                    node=node_obj,
                    connection_type=lc["connection_type"],
                    lorawan_device=LorawanDevice.objects.get(deveui=lc["lorawandevice"]["deveui"])
                )

    def createLorawanDevice(self, device):
        """
        Helper function which populates lorawan device test data.
        """
        for item in device:
            LorawanDevice.objects.create(
                deveui=item["deveui"], name=item["name"], hardware=SensorHardware.objects.get(hardware=item["hardware"])
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

class NodesViewSetTestCase(TestCase):
    def setUp(self):
        createComputeHardware(
            [
                {
                    "hardware": "xaviernx", 
                    "hw_model": "xavierNX",
                    "manufacturer": "ConnectTech",
                    "capabilities": [
                        "gpu",
                        "cuda102",
                        "arm64"
                    ]
                },
                {
                    "hardware": "rpi-8gb",
                    "hw_model": "RPI4B",
                    "manufacturer": "Raspberry Pi",
                    "capabilities": [
                        "arm64",
                        "poe"
                    ]
                },
            ]
        )

        createSensorHardware(
            [
                {
                    "hardware": "bme280", 
                    "hw_model": "BME280",
                    "manufacturer":"Bosch"
                },
                {
                    "hardware": "bme680", 
                    "hw_model": "BME680",
                    "manufacturer":"Bosch"
                },
                {
                    "hardware": "Arduino MKR WAN 1310", 
                    "hw_model": "MKR WAN 1310", 
                    "capabilities": ["lorawan"],
                    "manufacturer":"Arduino"
                },
                {
                    "hardware": "lorawan_2", 
                    "hw_model": "test_model", 
                    "capabilities": ["lorawan"],
                    "manufacturer":"Arduino"
                },
                {
                    "hardware": "ptz-8081",
                    "hw_model": "XNV-8081Z",
                    "manufacturer": "Hanwha Techwin",
                    "capabilities": ["camera"]
                },
            ]
        )

        createLorawanDevice(
            [
                {"deveui":"123","name":"CSU_soil_sensor","hardware":"Arduino MKR WAN 1310"},
                {"deveui":"111","name":"test","hardware":"lorawan_2"},
            ]
        )

        createProject(
            [
                {"name": "Sage"},
                {"name": "MyProject"}
            ]
        )

        createFocus(
            [
                {"name": "URBAN"},
                {"name": "MyFocus"}
            ]
        )

        createPartner(
            [
                {"name": "NU"},
                {"name": "MyPartner"}
            ]
        )

        createSite(
            [
                {"id": "ANL","description": "this site is argonne national lab"},
                {"id": "TEST","description": "this site is test"}
            ]
        )

        createAddress(
            [
                {   
                    "formatted": "9700 S Cass Ave, Lemont, IL 60439, USA",
                    "streetnum": "9700",
                    "route": "South Cass Avenue",
                    "town": "Lemont",
                    "state": "Illinois",
                    "state_code": "IL",
                    "postal_code": "60439",
                    "country": "United States",
                    "country_code": "US"
                },
                {
                    "formatted": "1234 brewer ln, St Charles, AZ 60411, USA",
                    "streetnum": "1234",
                    "route": "brewer ln",
                    "town": "St Charles",
                    "state": "Arizona",
                    "state_code": "AZ",
                    "postal_code": "60411",
                    "country": "United States",
                    "country_code": "US"
                },
                {
                    "formatted": "1235 Hathaway Dr, Sycamore, IL 60178, USA",
                    "streetnum": "1235",
                    "route": "Hathaway Drive",
                    "town": "Sycamore",
                    "state": "Illinois",
                    "state_code": "IL",
                    "postal_code": "60178",
                    "country": "United States",
                    "country_code": "US",
                },
            ]
        )

        createModem(
            [
                {
                    "sim_type": "anl-dawn",
                    "model": "mtcm2",
                    "carrier": "50501",
                    "iccid": "89610180004352783663",
                    "imsi": "505013549071214",
                    "imei": "860195053040081",
                },
                {
                    "sim_type": "anl-nu",
                    "model": "mtcm2",
                    "carrier": "",
                    "iccid": "",
                    "imsi": "",
                    "imei": "860195053079981",
                }
            ]
        )

        self.W123_data = {
                    "id": 1,
                    "vsn": "W123",
                    "name": "000048B02D0766BE",
                    "project": "Sage",
                    "focus": "MyFocus",
                    "partner": "MyPartner",
                    "gps_lat": 41.881832,
                    "gps_lon": -87.623177,
                    "gps_alt": 20.16849,
                    "type": "WSN",
                    "site_id": "ANL",
                    "addr_formatted": "9700 S Cass Ave, Lemont, IL 60439, USA",
                    "streetnum": "9700",
                    "route": "South Cass Avenue",
                    "town": "Lemont",
                    "state": "Illinois",
                    "state_code": "IL",
                    "postal_code": "60439",
                    "country": "United States",
                    "country_code": "US",
                    "location": "other notes on location",
                    "phase": "Maintenance",
                    "commissioned_at": "2023-02-23T23:47:35Z",
                    "registered_at": "2023-02-23T23:47:35Z",
                    "modem_sim": "anl-dawn",
                    "modem_model": "Multi-Tech MTCM2-L4G1-B03-KIT",
                    "modem_carrier": "50501",
                    "sensors": [
                        {
                            "name": "bottom_camera",
                            "hw_model": "XNV-8081Z",
                            "manufacturer": "Hanwha Techwin",
                            "capabilities": [
                                "camera"
                            ]
                        },
                        {
                            "name": "top_camera",
                            "hw_model": "XNV-8081Z",
                            "manufacturer": "Hanwha Techwin",
                            "capabilities": [
                                "camera"
                            ]
                        },
                        {
                            "name": "CSU_soil_sensor",
                            "hw_model": "MKR WAN 1310",
                            "manufacturer": "Arduino",
                            "capabilities": [
                                "lorawan"
                            ]
                        }
                    ],
                    "computes": [
                        {
                            "name": "nxcore",
                            "hw_model": "xavierNX",
                            "manufacturer": "ConnectTech",
                            "capabilities": [
                                "gpu",
                                "cuda102",
                                "arm64"
                            ]
                        },
                        {
                            "name": "rpi",
                            "hw_model": "RPI4B",
                            "manufacturer": "Raspberry Pi",
                            "capabilities": [
                                "arm64",
                                "poe"
                            ]
                        },
                        {
                            "name": "rpi.lorawan",
                            "hw_model": "RPI4B",
                            "manufacturer": "Raspberry Pi",
                            "capabilities": [
                                "arm64",
                                "poe"
                            ]
                        }
                    ],
                }

        self.W021_data = {
                    "id": 2,
                    "vsn": "W021",
                    "name": "000048B02D15BC77",
                    "project": "MyProject",
                    "focus": "MyFocus",
                    "partner": "MyPartner",
                    "type": "WSN",
                    "site_id": "TEST",
                    "gps_lat": 36.605171,
                    "gps_lon": -97.485585,
                    "gps_alt": 20.13246,
                    "addr_formatted": "1235 Hathaway Dr, Sycamore, IL 60178, USA",
                    "streetnum": "1235",
                    "route": "Hathaway Drive",
                    "town": "Sycamore",
                    "state": "Illinois",
                    "state_code": "IL",
                    "postal_code": "60178",
                    "country": "United States",
                    "country_code": "US",
                    "location": "test location",
                    "phase": "Deployed",
                    "commissioned_at": "2021-04-19T16:12:55Z",
                    "registered_at": "2021-04-19T16:12:55Z",
                    "modem_sim": "anl-nu",
                    "modem_model": "Multi-Tech MTCM2-L4G1-B03-KIT",
                    "modem_carrier": "",
                    "sensors": [
                        {
                            "name": "top_camera",
                            "hw_model": "XNV-8081Z",
                            "manufacturer": "Hanwha Techwin",
                            "capabilities": [
                                "camera"
                            ]
                        },
                        {
                            "name": "bottom_camera",
                            "hw_model": "XNV-8081Z",
                            "manufacturer": "Hanwha Techwin",
                            "capabilities": [
                                "camera"
                            ]
                        }
                    ],
                    "computes": [
                        {
                            "name": "nxcore",
                            "hw_model": "xavierNX",
                            "manufacturer": "ConnectTech",
                            "capabilities": [
                                "gpu",
                                "cuda102",
                                "arm64"
                            ]
                        },
                        {
                            "name": "rpi",
                            "hw_model": "RPI4B",
                            "manufacturer": "Raspberry Pi",
                            "capabilities": [
                                "arm64",
                                "poe"
                            ]
                        }
                    ]
                }

        createManifests([ self.W123_data, self.W021_data ])

    def test_retrieve_node(self):
        """Test node view's happy path for retrieving a record """
        r = self.client.get("/api/v-beta/nodes/W123/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(isinstance(data, dict)) #returns dict
        self.assertEqual(len(data), 29) #29 key-value pairs
        self.assertDictEqual(data,self.W123_data) 

    def test_retrieve_nodes(self):
        """Test nodes view's happy path for retrieving multiple records"""
        r = self.client.get("/api/v-beta/nodes/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 2) #2 nodes were created in setup()
        self.assertEqual(data[0]['vsn'], self.W021_data['vsn']) #ordered by vsn so W021 is index 0

    def test_project_url_filtering(self):
        """Test nodes view's url filtering for project"""
        r = self.client.get("/api/v-beta/nodes/?project__name=MyProject")
        data = r.json()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 1) #one node in this project
        self.assertEqual(data[0]['vsn'], self.W021_data['vsn'])

    def test_project_url_mult_filtering(self):
        """Test nodes view's url filtering for multiple projects"""
        r = self.client.get("/api/v-beta/nodes/?project__name=MyProject,Sage")
        data = r.json()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 2) #2 since one node in MyProject and other in Sage
        self.assertEqual(data[1]['vsn'], self.W123_data['vsn']) #ordered by vsn so W123 is index 1

    def test_phase_url_filtering(self):
        """Test nodes view's url filtering for phase"""
        r = self.client.get("/api/v-beta/nodes/?phase=Maintenance")
        data = r.json()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 1) #one node in this phase
        self.assertEqual(data[0]['vsn'], self.W123_data['vsn'])

    def test_phase_url_mult_filtering(self):
        """Test nodes view's url filtering for multiple phase"""
        r = self.client.get("/api/v-beta/nodes/?phase=Maintenance,Deployed")
        data = r.json()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 2) #2 since one node in Maint and other in Dep
        self.assertEqual(data[0]['vsn'], self.W021_data['vsn']) #ordered by vsn so W021 is index 0

    def test_mix_url_filtering(self):
        """Test nodes view's url filtering for multiple filters"""
        r = self.client.get("/api/v-beta/nodes/?project__name=MyProject,Sage&phase=Maintenance")
        data = r.json()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['vsn'], self.W123_data['vsn'])