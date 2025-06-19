"""Custom Django command to load manifest data using data scraped from nodes into the database."""

import os
from pathlib import Path
import subprocess
import json
from datetime import datetime
from environ import Env
from django.core.management.base import BaseCommand
from manifests.models import NodeData, Modem, Compute, ComputeSensor, Resource
from app.models import Node
import manifests.management.commands.mappers.compute_mappers as cm
import manifests.management.commands.mappers.sensor_mappers as sm
import manifests.management.commands.mappers.resource_mappers as rm


class Command(BaseCommand):
    help = """
    Load manifest data using data scraped from nodes into the database.
    SSH and scraping tools for nodes must be set up and working.
    """
    env = Env()

    def handle(self, *args, **options):
        """
        Handle the command execution.
        """
        self.set_constants(options)

        self.log("Starting manifest loading process...")

        # Get the list of VSNs to scrape/load
        vsns = self.get_vsns(options)

        # Scrape nodes and load manifests
        os.chdir(self.REPO_DIR)

        if not options["no_scrape"]:
            self.scrape_nodes(vsns)

        self.load_manifests(vsns)

        self.log("Manifest loading process completed.")

    def log(self, message):
        """
        Log messages.
        """
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.stdout.write(f"{timestamp} [INVENTORY_TOOLS]: {message}")

    def add_arguments(self, parser):
        """
        Add command line arguments for the command.
        """
        parser.add_argument(
            "--repo",
            type=str,
            default=self.env("INV_TOOLS_REPO", str, None),
            help="Inventory Tools Repository local path",
            required=True,
        )
        parser.add_argument(
            "--vsns",
            nargs="+",
            type=str,
            default=None,
            help="Optional list of VSNs to scrape/load. If not provided, all from DB will be used.",
        )
        parser.add_argument(
            "--no-scrape",
            action="store_true",
            default=False,
            help="If provided, will use existing manifest data and will not scrape nodes.",
        )

    def set_constants(self, options):
        """
        Set constants for the Command.
        """
        self.REPO_DIR = Path(options["repo"])
        self.DATA_DIR = Path(self.REPO_DIR, "data")

    def run_subprocess(self, cmd, cwd=None, input_data=None, shell=False):
        """
        Run subprocess command and stream output using logging.

        Args:
            cmd (list): Command to run as a list of arguments.
            cwd (str): Working directory for the command.
            input_data (str): Input data to write to stdin.
            shell (bool): Whether to run the command in a shell.
        """
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE if input_data else None,
            text=True,
            shell=shell,
            env=os.environ.copy(),
        )

        if input_data:
            process.stdin.write(input_data)
            process.stdin.close()

        for line in process.stdout:
            self.log(line.rstrip())

        return_code = process.wait()
        if return_code != 0:
            self.log(f"Command '{' '.join(cmd)}' exited with return code {return_code}")

    def get_vsns(self, options):
        """
        Get VSNs from the database or use provided list.
        """
        if options["vsns"]:
            self.log(f"Using provided VSNs: {options['vsns']}")
            return options["vsns"]
        else:
            self.log("Fetching all VSNs from database...")
            vsns = [
                p.parent.name
                for p in Path(options["repo"], "data").glob("*/manifest.json")
            ]
            return vsns

    def scrape_nodes(self, vsns):
        """
        Scrape node data using the scrape-nodes script.
        """
        script = Path(self.REPO_DIR, "scrape-nodes")
        try:
            self.run_subprocess(
                ["xargs", "-n1", "-P4", str(script)], input_data="\n".join(vsns)
            )
        except subprocess.CalledProcessError as e:
            self.log(f"Error running scrape-nodes: {e}")

    def load_manifests(self, vsns):
        """
        Load manifests into the database.
        """
        for vsn in vsns:
            manifest_path = Path(self.DATA_DIR, vsn, "manifest.json")
            if not manifest_path.exists():
                self.log(f"Missing manifest.json for {vsn}, skipping.")
                continue
            scraped = json.loads(manifest_path.read_text())
            node, _ = NodeData.objects.get_or_create(vsn=vsn)
            # update node and app-node
            self._sync_node_record(node, scraped)
            # update related models
            self._sync_modem(node, scraped)
            serials = self._sync_computes(node, scraped)
            # TODO Review whether we want to automatically deactivate computes.
            # self._deactivate_missing_computes(node, serials)
            self.log(f"Loaded manifest for {vsn}.")

    def _sync_node_record(self, node, data):
        """Sync base NodeData fields and app Node mac."""
        app_node, _ = Node.objects.get_or_create(vsn=node.vsn)
        # Update name (~node ID) for both the app and manifest node models, if exists in manifest.
        name = data.get("node_id")
        if name is not None:
            node.name = name
            node.save()
            app_node.mac = node.name
            app_node.save()

    def _sync_modem(self, node, data):
        """Create or update Modem from manifest"""
        modem = data.get("network", {}).get("modem", {}).get("3gpp", {})
        if not modem:
            return

        sim = data.get("network", {}).get("sim", {}).get("properties", {})
        if not sim:
            return

        Modem.objects.update_or_create(
            node=node,
            defaults={
                "imei": modem.get("imei"),
                "imsi": sim.get("imsi"),
                "iccid": sim.get("iccid"),
                "carrier": modem.get("operator_id", ""),
            },
        )

    def _sync_computes(self, node, data):
        """Upsert Compute, ComputeSensor, and Resource entries; return seen serials."""
        serials_seen = []
        for _, dev in data.get("devices", {}).items():
            serial = dev.get("serial")
            serials_seen.append(serial)

            if str(dev.get("reachable", "no")).lower() == "no":
                continue  # Skip unreachable devices

            hostname = dev.get("Static hostname", "")
            alias = cm.Resolve_compute_alias(hostname, dev)
            hardware = cm.Get_hardware_for_alias(alias, dev)

            compute_defaults = {
                "name": alias,
                "zone": dev.get("k8s", {}).get("labels", {}).get("zone"),
                "is_active": True,
                "hardware": hardware,
            }

            compute, _ = Compute.objects.update_or_create(
                node=node, serial_no=serial, defaults=compute_defaults
            )

            self._sync_compute_sensors(compute, dev)
            self._sync_node_resources(node, dev)

        return serials_seen

    def _sync_compute_sensors(self, comp, dev):
        """Upsert sensors for a Compute using abstracted mappings."""
        for mapper in sm.COMPUTE_SENSOR_MAPPERS:
            for name in mapper["sensor_names"](dev):
                hw = mapper["resolve_hardware"](name)
                ComputeSensor.objects.update_or_create(
                    scope=comp, name=name, defaults={"hardware": hw, "is_active": True}
                )

    def _sync_node_resources(self, node, dev):
        """Upsert resources for a node using abstracted mappings."""
        for mapper in rm.RESOURCE_MAPPERS:
            for name in mapper["resouce_names"](dev):
                hw = mapper["resolve_hardware"](name)
                Resource.objects.update_or_create(
                    node=node, name=name, defaults={"hardware": hw}
                )

    def _deactivate_missing_computes(self, node, saw):
        """Mark computes not in manifest as inactive"""
        for serial in Compute.objects.filter(node=node).values_list(
            "serial_no", flat=True
        ):
            if serial not in saw:
                Compute.objects.filter(node=node, serial_no=serial).update(
                    is_active=False
                )
