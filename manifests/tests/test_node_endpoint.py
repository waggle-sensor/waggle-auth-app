from django.test import TestCase
from manifests.models import *
from address.models import *
from pytest import mark
from ManifestHelp_fx import *

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