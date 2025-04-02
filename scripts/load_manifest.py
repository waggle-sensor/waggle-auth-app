"""
This script is used to load the manifest data into the database. 
Its purpose is to try to automize fields that are not dependent on user input.
"""
import os
import subprocess
import json
import shutil
import logging
from manifests.models import NodeData, Modem, Compute, ComputeSensor #TODO: Also do auth app node model
from django.conf import settings
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INVENTORY_TOOLS]: %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
logger = logging.getLogger(__name__)

# Check if INVENTORY_TOOLS is set in settings
if not hasattr(settings, 'INVENTORY_TOOLS') or not settings.INVENTORY_TOOLS:
    logging.info("INVENTORY_TOOLS setting is not set. Manifest loading will not proceed.")
    exit(0)

# Set up constants
INVENTORY_REPO = settings.INVENTORY_TOOLS
WORKDIR = "/app"
REPO_DIR = os.path.join(WORKDIR, "waggle-inventory-tools")
DATA_DIR = os.path.join(REPO_DIR, "data")

def get_repo():
    """
    Clone the inventory tools repository if it doesn't exist, or pull the latest changes.
    """
    #clone repo
    if os.path.exists(REPO_DIR) and os.path.samefile(REPO_DIR, os.getcwd()):
        logging.info("Skipping clone, already in the inventory tools repo.")
    else:
        if os.path.exists(REPO_DIR):
            shutil.rmtree(REPO_DIR)
        subprocess.run(["git", "clone", INVENTORY_REPO, REPO_DIR], check=True)

    # Pull latest
    subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

def get_vsns():
    """
    Get all node VSNs from the database.
    """
    # Get all node VSNs from DB
    vsns = NodeData.objects.values_list("vsn", flat=True)
    return vsns

def scrape_nodes(vsns):
    """
    Scrape node data using the scrape-nodes script.
    """
    # Scrape each node
    scrape_script = os.path.join(REPO_DIR, "scrape-nodes")
    process = subprocess.run(["xargs", "-n1", "-P4", scrape_script], input="\n".join(vsns), text=True)

def load_manifests(vsns):
    """
    Load manifests into the database.
    """

    # Process scraped data
    for vsn in vsns:
        manifest_path = os.path.join(DATA_DIR, vsn, "manifest.json")
        if not os.path.exists(manifest_path):
            logging.info(f"Missing manifest for {vsn}, skipping.")
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

def main():
    logging.info("Starting manifest loading process...")
    os.chdir(WORKDIR)
    
    # Step 1: Get repo
    get_repo()
    
    # Step 2: Get vsns
    vsns = get_vsns()
    
    # Step 3: Scrape nodes
    scrape_nodes(vsns)
    
    # Step 4: Load manifests
    load_manifests(vsns)
    
    logging.info("Manifest loading process completed.")

if __name__ == "__main__":
    main()

# --- 10) Add to cron ---
# Cron job setup should be handled outside this script, for example:
# */30 * * * * /usr/bin/env python3 /app/scripts/load_manifest.py >> /var/log/load_manifest.log 2>&1

# NOTE: 
# - The scraped node data will go into the directory /app/waggle-inventory-tools/data/<vsn>/. 
# /app/waggle-inventory-tools/data will be an attached volume to systems' /etc/waggle/manifest so users can access it outside of the container/pod.