"""Custom Django command to load manifest data using data scraped from nodes into the database."""
import os
import subprocess
import json
from datetime import datetime
from environ import Env
from django.core.management.base import BaseCommand
from manifests.models import NodeData, Modem, Compute, ComputeSensor #TODO: Also do auth app node model

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
        parser.add_argument("--repo", type=str, default=self.env("INV_TOOLS_REPO", str, None), help="Inventory Tools Repository local path", required=True)
        parser.add_argument("--vsns", nargs="+", type=str, default=None, help="Optional list of VSNs to scrape/load. If not provided, all from DB will be used.")

    def set_constants(self, options):
        """
        Set constants for the Command.
        """
        self.REPO_DIR = options["repo"]
        self.DATA_DIR = os.path.join(self.REPO_DIR, "data")

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
            return NodeData.objects.values_list("vsn", flat=True)

    def scrape_nodes(self, vsns):
        """
        Scrape node data using the scrape-nodes script.
        """
        script = os.path.join(self.REPO_DIR, "scrape-nodes")
        try:
            self.run_subprocess(["xargs", "-n1", "-P4", script], input_data="\n".join(vsns))
        except subprocess.CalledProcessError as e:
            self.log(f"Error running scrape-nodes: {e}")

    def load_manifests(self, vsns):
        """
        Load manifests into the database.
        """
        for vsn in vsns:
            manifest_path = os.path.join(self.DATA_DIR, vsn, "manifest.json")
            if not os.path.exists(manifest_path):
                self.log(f"Missing scrape-nodes's manifest.json for {vsn}, skipping.")
                continue

            with open(manifest_path) as f:
                scraped_data = json.load(f)

            node, _ = NodeData.objects.get_or_create(vsn=vsn)
            node.name = scraped_data.get("node_id")
            node.save()

            # # Update Modem
            # modem_data = scraped_data.get("network", {}).get("modem", {}).get("3gpp", {})
            # sim_data = scraped_data.get("network", {}).get("sim", {}).get("properties", {})
            # Modem.objects.update_or_create(
            #     node=node,
            #     defaults={
            #         "imei": modem_data.get("imei"),
            #         "imsi": sim_data.get("imsi"),
            #         "iccid": sim_data.get("iccid"),
            #         "carrier": sim_data.get("operator_id"),
            #     },
            # )

            # # Update Compute
            # device_data = scraped_data.get("devices", {})
            # hostname = device_data.get("Static hostname", "")
            # serial = device_data.get("serial")
            # zone = device_data.get("k8s", {}).get("labels", {}).get("zone")
            # kernel_modules = device_data.get("kernel_modules", [])
            # module_names = [m.get("name") for m in kernel_modules]

            # if "nxcore" in hostname:
            #     compute_name = "nxcore"
            # elif "ws-rpi" in hostname:
            #     compute_name = "rpi"
            # elif module_names.count("spidev") >= 2:
            #     compute_name = "rpi.lorawan"
            # else:
            #     compute_name = ""

            # Compute.objects.update_or_create(
            #     node=node,
            #     defaults={
            #         "name": compute_name,
            #         "serial_no": serial,
            #         "zone": zone,
            #         # TODO: define how to extract hardware info
            #     },
            # )

            # # Update ComputeSensor
            # iio_devs = device_data.get("iio_devices", [])
            # sensors = []
            # if "bme280" in iio_devs:
            #     sensors.append("bme280")
            # if module_names.count("spidev") >= 2:
            #     sensors.append("lorawan")

            # for sensor_name in sensors:
            #     ComputeSensor.objects.update_or_create(
            #         scope=serial,
            #         name=sensor_name,
            #         defaults={
            #             # TODO: define how to extract hardware info
            #         },
            #     )