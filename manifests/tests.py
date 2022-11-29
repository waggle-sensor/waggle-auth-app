from django.test import TestCase
from .models import *
import json


class HomepageTest(TestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/manifests/")
        self.assertEqual(response.status_code, 200)


class ManifestTest(TestCase):
    def setUp(self):
        self.Node = NodeData.objects.create(vsn="A", name="A_name", gps_lat=50.00, gps_lon=50.00)

        tag1 = Tag.objects.create(tag="t1")
        self.Node.tags.set([tag1.pk])

        compute1 = Hardware.objects.create(hardware="h1")
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

    def test_contains_expected_fields(self):
        r = self.client.get("/manifests/")
        data = json.loads(r.content)
        self.assertEqual(data[0].keys(), set(['vsn', 'name', 'resources', 'sensors', 'gps_lat', 'gps_lon', 'tags', 'computes']))

    def test_get_manifest(self):
        self.createHardware([
            {"hardware": "nx1", "hw_model": "Nvidia Jetson Xavier"},
            {"hardware": "rpi4", "hw_model": "Raspberry PI 4"},
            {"hardware": "bme280", "hw_model": "BME280"},
            {"hardware": "bme680", "hw_model": "BME680"},
        ])

        self.createManifests([
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
                ]
            },
        ])

        r = self.client.get("/manifests/W123/")
        self.assertEqual(r.status_code, 200)
        manifest = data = r.json()

        self.assertManifestContainsSubset(manifest, {
            "vsn": "W123",
            "gps_lat": 41.881832,
            "gps_lon": -87.623177,
            "computes": [
                {
                    "name": "nxcore",
                    "hardware": {
                        "hardware": "nx1",
                        "hw_model": "Nvidia Jetson Xavier",
                    }
                },
                {
                    "name": "nxagent",
                    "hardware": {
                        "hardware": "nx1",
                        "hw_model": "Nvidia Jetson Xavier",
                    }
                },
                {
                    "name": "rpi",
                    "hardware": {
                        "hardware": "rpi4",
                        "hw_model": "Raspberry PI 4",
                    }
                },
            ],
        })

    def createHardware(self, hardware):
        """
        Helper function which populates hardware test data.
        """
        for item in hardware:
            Hardware.objects.create(hardware=item["hardware"], hw_model=item["hw_model"])

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
                    hardware=Hardware.objects.get(hardware=compute["hardware"]),
                    name=compute["name"],
                )
                for sensor in compute["sensors"]:
                    ComputeSensor.objects.create(
                        hardware=Hardware.objects.get(hardware=sensor),
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
