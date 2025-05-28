import os
import json
import tempfile
import shutil
import subprocess
from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from manifests.models import NodeData, Modem, Compute, ComputeSensor, ComputeHardware, Resource
from app.models import Node as AppNode
from manifests.models import SensorHardware
from unittest.mock import patch, MagicMock
from manifests.management.commands.loadmanifest import Command

class LoadManifestCommandTestCase(TestCase):
    def setUp(self):
        # create temporary repo dir with data structure inventory-tools outputs
        self.tmpdir = tempfile.mkdtemp()
        data_dir = os.path.join(self.tmpdir, 'data')
        os.makedirs(data_dir)
        # create ComputeHardware entries
        ComputeHardware.objects.create(hardware='xaviernx')
        ComputeHardware.objects.create(hardware='rpi-4gb')
        # create SensorHardware entries for IIO, label, and LoRa sensors
        SensorHardware.objects.create(hardware='sensor1')
        SensorHardware.objects.create(hardware='abc')
        SensorHardware.objects.create(hardware='lorawan')
        SensorHardware.objects.create(hardware='LoRa Fiber Glass Antenna')

        # prepare a manifest for vsn 'V1'
        self.vsn = 'V1'
        vsn_dir = os.path.join(data_dir, self.vsn)
        os.makedirs(vsn_dir)
        manifest = {
            "vsn": self.vsn,
            "reachable": "yes",
            "node_id": "MAC123",
            "network": {
                "modem": {"3gpp": {"imei": "111222333444555", "operator_id": "310410"}},
                "sim": {"properties": {"imsi": "999888777666555", "iccid": "12345678901234567890"}}
            },
            "devices": {
                "dev1": {
                    "reachable": "yes",
                    "serial": "SERIAL1",
                    "Static hostname": "ws-nxcore-foo",
                    "k8s": {"labels": {"zone": "core"}},
                    "iio_devices": ["sensor1"],
                    "lora_gws": ["gw1"],
                    "waggle_devices": [
                        {
                        "id": "waggle-core-switchconsole",
                        "path": "/dev/waggle-core-switchconsole",
                        "target": "ttyUSB0",
                        "permissions": "lrwxrwxrwx",
                        "owner": "root",
                        "group": "root",
                        "timestamp": "May 13 18:26",
                        "timestamp_iso": "2025-05-13T18:26:00"
                        }
                    ]
                }
            }
        }
        with open(os.path.join(vsn_dir, 'manifest.json'), 'w') as f:
            json.dump(manifest, f)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_loadmanifest_creates_models(self):
        # run the management command
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', self.vsn)
        # NodeData created
        nd = NodeData.objects.get(vsn=self.vsn)
        self.assertEqual(nd.name, 'MAC123')
        # App Node mac set
        an = AppNode.objects.get(vsn=self.vsn)
        self.assertEqual(an.mac, 'MAC123')
        # Modem created
        modem = Modem.objects.get(node=nd)
        self.assertEqual(modem.imei, '111222333444555')
        self.assertEqual(modem.imsi, '999888777666555')
        self.assertEqual(modem.iccid, '12345678901234567890')
        self.assertEqual(modem.carrier, '310410')
        # Compute created
        comp = Compute.objects.get(node=nd, serial_no='SERIAL1')
        self.assertEqual(comp.name, 'nxcore')
        # IIO sensor
        sensor1 = ComputeSensor.objects.get(scope=comp, name='sensor1')
        self.assertTrue(sensor1.is_active)
        # LoRa sensors
        lor = ComputeSensor.objects.get(scope=comp, name='lorawan')
        ant = ComputeSensor.objects.get(scope=comp, name='Lorawan Antenna')
        self.assertTrue(lor.is_active)
        self.assertTrue(ant.is_active)
        # Resource created
        switch = Resource.objects.get(node=nd, name='switch')
        self.assertEqual(switch.name, 'switch')

    def test_missing_manifest_skips(self):
        """Test that missing manifest.json files are skipped without error."""
        # call with non-existent vsn should not error
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', 'MISSING')
        self.assertFalse(NodeData.objects.filter(vsn='MISSING').exists())

    def test_get_vsns_with_vsns_option(self):
        """Test that --vsns option is used to fetch vsns."""
        # Run command with explicit --vsns argument
        out = StringIO()
        vsn_list = ['A', 'B', 'C']
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', *vsn_list, stdout=out)
        output = out.getvalue()
        # Should log using provided vsns
        self.assertIn(f"Using provided VSNs: {vsn_list}", output)
        # Should attempt to skip missing manifest for each vsn
        for vsn in vsn_list:
            self.assertIn(f"Missing manifest.json for {vsn}, skipping.", output)

    def test_get_vsns_without_option_fetches_db(self):
        """Test the get all vsns from DB if --vsns not provided."""
        # create NodeData entries in DB
        NodeData.objects.create(vsn='X1')
        NodeData.objects.create(vsn='X2')
        out = StringIO()
        call_command('loadmanifest', '--repo', self.tmpdir, stdout=out)
        output = out.getvalue()
        # Should log fetching from DB
        self.assertIn("Fetching all VSNs from database...", output)
        # Should skip manifests for each vsn
        for vsn in ['X1', 'X2']:
            self.assertIn(f"Missing manifest.json for {vsn}, skipping.", output)

    @patch.object(Command, 'run_subprocess', side_effect=subprocess.CalledProcessError(1, 'scrape-nodes'))
    def test_scrape_nodes_handles_called_process_error(self, mock_run_subprocess):
        """Test that scrape_nodes handles CalledProcessError gracefully."""
        # Arrange
        command = Command()
        command.REPO_DIR = self.tmpdir
        command.stdout = StringIO()  # Capture logs
        vsns = ['V3']

        # Act
        command.scrape_nodes(vsns)

        # Assert
        output = command.stdout.getvalue()
        self.assertIn("Error running scrape-nodes", output)

    def test_all_compute_alias_types(self):
        """Ensure each hostname pattern maps to the correct compute alias."""
        # prepare new VSN with multiple device types
        vsn2 = 'V2'
        data_dir = os.path.join(self.tmpdir, 'data')
        v2_dir = os.path.join(data_dir, vsn2)
        os.makedirs(v2_dir)
        # add missing ComputeHardware for mapping
        for hw in ['rpi-8gb', 'dell-xr2', 'xaviernx-poe']:
            ComputeHardware.objects.create(hardware=hw)
        manifest = {
            'node_id': 'MAC456',
            'network': {'modem': {}, 'sim': {}},
            'devices': {
                'd_nxcore': {'reachable': 'yes', 'serial': 'S1', 'Static hostname': 'ws-nxcore-abc', 'k8s': {'labels': {'zone': 'z'}}, 'iio_devices': [], 'lora_gws': []},
                'd_sb': {'reachable': 'yes', 'serial': 'S2', 'Static hostname': 'host-sb-core-01', 'k8s': {'labels': {'zone': 'z'}}, 'iio_devices': [], 'lora_gws': []},
                'd_agent': {'reachable': 'yes', 'serial': 'S3', 'Static hostname': 'x-nxagent-x', 'k8s': {'labels': {'zone': 'z'}}, 'iio_devices': [], 'lora_gws': []},
                'd_rpi': {'reachable': 'yes', 'serial': 'S4', 'Static hostname': 'foo-ws-rpi-bar', 'k8s': {'labels': {'zone': 'z'}}, 'iio_devices': [], 'lora_gws': []},
                'd_lora': {'reachable': 'yes', 'serial': 'S5', 'Static hostname': 'xx-ws-rpi-yy', 'k8s': {'labels': {'zone': 'z'}}, 'iio_devices': [], 'lora_gws': ['gw']},
                'd_custom': {'reachable': 'yes', 'serial': 'S6', 'Static hostname': 'some-host', 'k8s': {'labels': {'zone': 'z'}}, 'iio_devices': [], 'lora_gws': []},
            }
        }
        with open(os.path.join(v2_dir, 'manifest.json'), 'w') as f:
            json.dump(manifest, f)
        # run command
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', vsn2)
        # lookup and assert each alias
        expected = {'S1': 'nxcore', 'S2': 'sbcore', 'S3': 'nxagent', 'S4': 'rpi', 'S5': 'rpi.lorawan', 'S6': 'custom'}
        for serial, alias in expected.items():
            comp = Compute.objects.get(serial_no=serial)
            self.assertEqual(comp.name, alias, f"Serial {serial} should map to {alias}")

    def test_deactivate_missing_computes(self):
        """Ensure computes absent from manifest are marked inactive."""
        # initial load creates only SERIAL1
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', self.vsn)
        nd = NodeData.objects.get(vsn=self.vsn)
        # create an extra compute not in manifest
        extra_hw, _ = ComputeHardware.objects.get_or_create(hardware='custom')
        extra = Compute.objects.create(
            node=nd,
            serial_no='EXTRA',
            name='custom',
            zone='z',
            is_active=True,
            hardware=extra_hw,
        )
        # re-run load to trigger deactivation
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', self.vsn)
        extra.refresh_from_db()
        # EXTRA should now be inactive
        self.assertFalse(extra.is_active)
        # original compute remains active
        comp = Compute.objects.get(node=nd, serial_no='SERIAL1')
        self.assertTrue(comp.is_active)
    
    def test_unreachable_devices_skipped(self):
        """Ensure unreachable devices are skipped."""
        # prepare manifest with an unreachable device
        vsn3 = 'V3'
        v3_dir = os.path.join(self.tmpdir, 'data', vsn3)
        os.makedirs(v3_dir)
        manifest = {
            "vsn": vsn3,
            "reachable": "yes",
            "node_id": "MAC789",
            "network": {"modem": {}, "sim": {}},
            "devices": {
                "dev1": {
                    "reachable": "no",  # this device should be skipped
                    "serial": "SERIAL2",
                    "Static hostname": "ws-nxcore-unreachable",
                    "k8s": {"labels": {"zone": "core"}},
                    "iio_devices": [],
                    "lora_gws": []
                }
            }
        }
        with open(os.path.join(v3_dir, 'manifest.json'), 'w') as f:
            json.dump(manifest, f)
        # run command
        call_command('loadmanifest', '--repo', self.tmpdir, '--vsns', vsn3)
        # no Compute should be created for unreachable device
        self.assertFalse(Compute.objects.filter(node__vsn=vsn3).exists())