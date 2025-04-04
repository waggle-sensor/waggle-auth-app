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

# Check if INV_TOOLS_REPO is set in settings
if not hasattr(settings, 'INV_TOOLS_REPO') or not settings.INV_TOOLS_REPO:
    logging.info("INV_TOOLS_REPO setting is not set. Manifest loading will not proceed.")
    exit(0)

# Set up constants
WORKDIR = "/app"
REPO_URL = settings.INV_TOOLS_REPO
REPO_VERSION = settings.INV_TOOLS_VERSION
REPO_DIR = os.path.join(WORKDIR, "waggle-inventory-tools")
DATA_DIR = os.path.join(REPO_DIR, "data")

def is_commit_sha(ref):
    """Return True if ref looks like a git commit SHA."""
    return len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref.lower())

def get_repo():
    """
    Clone the inventory tools repository if it doesn't exist, or use the cached one.
    Then checkout the specified version (branch, tag, or commit SHA).
    """
    if not os.path.exists(REPO_DIR):
        logging.info(f"Cloning repo from {REPO_URL} to {REPO_DIR}")
        subprocess.run(["git", "clone", REPO_URL, REPO_DIR], check=True)
    else:
        logging.info(f"Using cached repo at {REPO_DIR}")
        # Just ensure we fetch all remote info
        subprocess.run(["git", "-C", REPO_DIR, "fetch", "--all", "--tags"], check=True)

    if REPO_VERSION is None:
        logging.info("Using latest version from default branch.")
        subprocess.run(["git", "-C", REPO_DIR, "checkout", "main"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "pull", "origin", "main"], check=True)
    else:
        logging.info(f"Checking out version: {REPO_VERSION}")
        subprocess.run(["git", "-C", REPO_DIR, "fetch", "--all", "--tags"], check=True)

        if is_commit_sha(REPO_VERSION):
            subprocess.run(["git", "-C", REPO_DIR, "checkout", REPO_VERSION], check=True)
        else:
            # Check if it's a branch
            result = subprocess.run(["git", "-C", REPO_DIR, "rev-parse", "--verify", f"origin/{REPO_VERSION}"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                subprocess.run(["git", "-C", REPO_DIR, "checkout", REPO_VERSION], check=True)
                subprocess.run(["git", "-C", REPO_DIR, "pull", "origin", REPO_VERSION], check=True)
            else:
                # Try tag
                subprocess.run(["git", "-C", REPO_DIR, "checkout", f"tags/{REPO_VERSION}"], check=True)

def get_vsns():
    """
    Get all node VSNs from the database.
    """
    # Get all node VSNs from DB
    #TODO: Get rid of the circular dependency here, inventory tools wont run unless node 
    # is added to manifest app which is what we are trying to update with INVENTORY_TOOLS
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