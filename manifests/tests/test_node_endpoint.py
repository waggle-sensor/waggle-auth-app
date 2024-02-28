from django.test import TestCase
from manifests.models import *
from address.models import *
from pytest import mark

@mark.rn
class NodesViewSetTestCase(TestCase):
    def setUp(self):
        self.createComputeHardware(
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

        self.createSensorHardware(
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

        self.createLorawanDevice(
            [
                {"deveui":"123","name":"CSU_soil_sensor","hardware":"Arduino MKR WAN 1310"},
                {"deveui":"111","name":"test","hardware":"lorawan_2"},
            ]
        )

        self.createProject(
            [
                {"name": "Sage"},
                {"name": "MyProject"}
            ]
        )

        self.createFocus(
            [
                {"name": "URBAN"},
                {"name": "MyFocus"}
            ]
        )

        self.createPartner(
            [
                {"name": "NU"},
                {"name": "MyPartner"}
            ]
        )

        self.createSite(
            [
                {"id": "ANL","description": "this site is argonne national lab"},
                {"id": "TEST","description": "this site is test"}
            ]
        )

        self.createAddress(
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

        self.createModem(
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

        self.createManifests(
            [
                {
                    "id": 717,
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
                    "address_formatted": "9700 S Cass Ave, Lemont, IL 60439, USA",
                    "address_streetnum": "9700",
                    "address_route": "South Cass Avenue",
                    "address_town": "Lemont",
                    "address_state": "Illinois",
                    "address_state_code": "IL",
                    "address_postal_code": "60439",
                    "address_country": "United States",
                    "address_country_code": "US",
                    "location": "other notes on location",
                    "phase": "Deployed",
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
                },
                {
                    "id": 701,
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
                    "address_formatted": "1235 Hathaway Dr, Sycamore, IL 60178, USA",
                    "address_streetnum": "1235",
                    "address_route": "Hathaway Drive",
                    "address_town": "Sycamore",
                    "address_state": "Illinois",
                    "address_state_code": "IL",
                    "address_postal_code": "60178",
                    "address_country": "United States",
                    "address_country_code": "US",
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
                },
            ]
        )

    def createComputeHardware(self, hardware):
        """
        Helper function which populates compute hardware test data.
        """
        for item in hardware:
            compute_hardware = ComputeHardware.objects.create(
                hardware=item["hardware"], 
                hw_model=item["hw_model"],
                manufacturer=item['manufacturer']
            )

        if "capabilities" in item:
            for name in item["capabilities"]:
                capability, _ = Capability.objects.get_or_create(capability=name)
                compute_hardware.capabilities.add(capability)

    def createSensorHardware(self, hardware):
        """
        Helper function which populates sensor hardware test data.
        """
        for item in hardware:
            sensor_hardware = SensorHardware.objects.create(
                hardware=item["hardware"], 
                hw_model=item["hw_model"],
                manufacturer=item['manufacturer']
            )

        if "capabilities" in item:
            for name in item["capabilities"]:
                capability, _ = Capability.objects.get_or_create(capability=name)
                sensor_hardware.capabilities.add(capability)

    def createLorawanDevice(self, device):
        """
        Helper function which populates lorawan device test data.
        """
        for item in device:
            LorawanDevice.objects.create(
                deveui=item["deveui"], name=item["name"], 
                hardware=SensorHardware.objects.get(hardware=item["hardware"])
            )

    def createProject(self, project):
        """
        Helper function which populates project test data.
        """
        for item in project:
            NodeBuildProject.objects.create(
                name=item['name']
            )

    def createFocus(self, focus):
        """
        Helper function which populates focus test data.
        """
        for item in focus:
            NodeBuildProjectFocus.objects.create(
                name=item['name']
            )

    def createPartner(self, partner):
        """
        Helper function which populates partner test data.
        """
        for item in partner:
            NodeBuildProjectPartner.objects.create(
                name=item['name']
            )

    def createSite(self, site):
        """
        Helper function which populates site test data.
        """
        for item in site:
            Site.objects.create(
                id=item['id'], description=item['description']
            )

    def createAddress(self, address):
        """
        Helper function which populates address test data.
        """
        for item in address:
            Country.objects.get_or_create(
                name= item['country'], code=item['country_code']
            )

            State.objects.get_or_create(
                name= item['state'], code=item['state_code'],
                country=Country.objects.get(name=item['country'])
            )

            Locality.objects.get_or_create(
                name= item['town'], postal_code=item['postal_code'],
                state=State.objects.get(name=item['state'])
            )

            Address.objects.get_or_create(
                street_number=item['streetnum'],route=item['route'], formatted=item['formatted'],
                locality=Locality.objects.get(postal_code=item['postal_code'])
            )

    def createModem(self, modem):
        """
        Helper function which populates modem test data.
        """        
        for item in modem:
            Modem.objects.create(
                imei=item['imei'],imsi=item['imsi'],
                iccid=item['iccid'],carrier=item['carrier'],
                model=item['model'],sim_type=item['sim_type']
            )

    def createManifests(self, manifests):
        """
        Helper function which populates manifest test data.
        """
        for manifest in manifests:
            node_obj = NodeData.objects.create(
                vsn=manifest["vsn"],
                name=manifest["name"],
                gps_lat=manifest["gps_lat"],
                gps_lon=manifest["gps_lon"],
                gps_alt=manifest["gps_alt"],
                project=NodeBuildProject.objects.get(name=manifest['project']),
                focus=NodeBuildProjectFocus.objects.get(name=manifest['focus']),
                partner=NodeBuildProjectPartner.objects.get(name=manifest['partner']),
                type=manifest['type'],
                site_id=Site.objects.get(id=manifest['site_id']),
                address=Address.objects.get(formatted=manifest['address_formatted']),
                location=manifest["location"],
                phase=manifest['phase'],
                commissioned_at=manifest['commissioned_at'],
                registered_at=manifest['registered_at']
            )
            #update modem
            modem = Modem.objects.get(sim_type=manifest['modem_sim'])
            modem.node = node_obj
            modem.save()
            for sensor in manifest['sensors']:
                if "lorawan" in sensor['capabilities']:
                    LorawanConnection.objects.create(
                        node=node_obj,
                        connection_type="OTAA", #in this view con_type does not matter so set a static val
                        lorawan_device=LorawanDevice.objects.get(name=sensor['name'])
                    )
                else:
                    NodeSensor.objects.create(
                        node=node_obj,
                        name=sensor['name'],
                        hardware=SensorHardware.objects.get(hw_model=sensor['hw_model'])
                    )
            for compute in manifest["computes"]:
                compute_obj = Compute.objects.create(
                    node=node_obj,
                    hardware=ComputeHardware.objects.get(hw_model=compute["hw_model"]),
                    name=compute["name"],
                )

    def test_retrieve_node(self):
        """Test node view for retrieving a record happy path"""

        r = self.client.get("/api/v-beta/nodes/W030")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)