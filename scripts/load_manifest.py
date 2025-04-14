"""
This script is used to load the manifest data into the database. 
Its purpose is to try to automize fields that are not dependent on user input.
"""
import os
import subprocess
import json
import re
import logging
from manifests.models import NodeData, Modem, Compute, ComputeSensor #TODO: Also do auth app node model
from django.conf import settings
logging.basicConfig(level=logging.INFO, format="%(asctime)s [INVENTORY_TOOLS]: %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
logger = logging.getLogger(__name__)

# Check if INVENTORY_TOOLS keys are set in settings
if not hasattr(settings, 'INV_TOOLS_REPO') or not settings.INV_TOOLS_REPO:
    logging.info("INV_TOOLS_REPO setting is not set. Manifest loading will not proceed.")
    exit(0)
elif not hasattr(settings, 'INV_TOOLS_TOKEN') or not settings.INV_TOOLS_TOKEN:
    logging.info("INV_TOOLS_TOKEN setting is not set. Manifest loading will not proceed.")
    exit(0)
elif not hasattr(settings, 'INV_TOOLS_SSH_TOOLS') or not settings.INV_TOOLS_SSH_TOOLS:
    logging.info("INV_TOOLS_SSH_TOOLS setting is not set. Manifest loading will not proceed.")
    exit(0)
elif not hasattr(settings, 'INV_TOOLS_SSH_CONFIG') or not settings.INV_TOOLS_SSH_CONFIG:
    logging.info("INV_TOOLS_SSH_CONFIG setting is not set. Manifest loading will not proceed.")
    exit(0)
elif not hasattr(settings, 'INV_TOOLS_SSH_TOOLS_PW') or not settings.INV_TOOLS_SSH_TOOLS_PW:
    logging.info("INV_TOOLS_SSH_TOOLS_PW setting is not set. Manifest loading will not proceed.")
    exit(0)

# Set up constants
WORKDIR = "/app"
REPO_URL = settings.INV_TOOLS_REPO
REPO_VERSION = settings.INV_TOOLS_VERSION
REPO_TOKEN = settings.INV_TOOLS_TOKEN
SSH_PWD = settings.INV_TOOLS_SSH_TOOLS_PW
SSH_TOOLS_DIR = settings.INV_TOOLS_SSH_TOOLS
SSH_TEMPLATE = settings.INV_TOOLS_SSH_CONFIG
REPO_DIR = os.path.join(WORKDIR, "waggle-inventory-tools")
DATA_DIR = os.path.join(REPO_DIR, "data")
SSH_CONFIG_TEMPLATE = os.path.join(SSH_TEMPLATE, "config")
HONEYHOUSE_DIR = os.path.join(SSH_TOOLS_DIR, "honeyhouse-config")
PRIV_CONFIG_DIR = os.path.join(SSH_TOOLS_DIR, "private_config")
DEVOPS_DIR = os.path.join(SSH_TOOLS_DIR, "devOps")

#check if the ssh directory is correctly set up
if not os.path.exists(SSH_TEMPLATE):
    logging.info(f"SSH directory {SSH_TEMPLATE} does not exist. Manifest loading will not proceed.")
    exit(0)
elif not os.path.exists(SSH_CONFIG_TEMPLATE):
    logging.info(f"SSH config file {SSH_CONFIG_TEMPLATE} does not exist. Manifest loading will not proceed.")
    exit(0)
elif not os.path.exists(HONEYHOUSE_DIR):
    logging.info(f"SSH IdentityFile {HONEYHOUSE_DIR} does not exist. Manifest loading will not proceed.")
    exit(0)
elif not os.path.exists(PRIV_CONFIG_DIR):
    logging.info(f"SSH IdentityFile {PRIV_CONFIG_DIR} does not exist. Manifest loading will not proceed.")
    exit(0)
elif not os.path.exists(DEVOPS_DIR):
    logging.info(f"SSH ProxyCommand {DEVOPS_DIR} does not exist. Manifest loading will not proceed.")
    exit(0)

def is_commit_sha(ref):
    """Return True if ref looks like a git commit SHA."""
    return len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref.lower())

def run_subprocess(cmd, cwd=None, input_data=None, shell=False):
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

    assert process.stdout is not None
    if input_data:
        assert process.stdin is not None
        process.stdin.write(input_data)
        process.stdin.close()

    for line in process.stdout:
        logging.info(line.rstrip())

    return_code = process.wait()
    if return_code != 0:
        logging.info(f"Command '{' '.join(cmd)}' exited with return code {return_code}")

def get_repo():
    """
    Clone the inventory tools repository if it doesn't exist, or use the cached one.
    Then checkout the specified version (branch, tag, or commit SHA).
    """
    auth_repo_url = REPO_URL.replace("https://", f"https://{REPO_TOKEN}@")

    if not os.path.exists(REPO_DIR):
        logging.info(f"Cloning repo from {REPO_URL} to {REPO_DIR}")
        run_subprocess(["git", "clone", auth_repo_url, REPO_DIR])
        run_subprocess(["git", "config", "--global", "--add", "safe.directory", REPO_DIR])
    else:
        logging.info(f"Using cached repo at {REPO_DIR}")
        run_subprocess(["git", "config", "--global", "--add", "safe.directory", REPO_DIR])
        run_subprocess(["git", "-C", REPO_DIR, "fetch", "--all", "--tags"]) 

    if REPO_VERSION is None:
        logging.info("Using latest version from default branch.")
        run_subprocess(["git", "-C", REPO_DIR, "checkout", "main"])
        run_subprocess(["git", "-C", REPO_DIR, "pull", "origin", "main"])
    else:
        logging.info(f"Checking out version: {REPO_VERSION}")
        run_subprocess(["git", "-C", REPO_DIR, "fetch", "--all", "--tags"])

        if is_commit_sha(REPO_VERSION):
            run_subprocess(["git", "-C", REPO_DIR, "checkout", REPO_VERSION])
        else:
            # Check if it's a branch
            result = subprocess.run(["git", "-C", REPO_DIR, "rev-parse", "--verify", f"origin/{REPO_VERSION}"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                run_subprocess(["git", "-C", REPO_DIR, "checkout", REPO_VERSION])
                run_subprocess(["git", "-C", REPO_DIR, "pull", "origin", REPO_VERSION])
            else:
                run_subprocess(["git", "-C", REPO_DIR, "checkout", f"tags/{REPO_VERSION}"])
    # Go to the repo directory
    os.chdir(REPO_DIR)

def set_ssh():
    """
    Set up SSH configuration for the nodes.
    """
    ssh_dir = os.path.expanduser("~/.ssh")
    ssh_config = os.path.join(ssh_dir, "config")
    ssh_key_path = os.path.join(PRIV_CONFIG_DIR ,"misc/waggle-sage/ecdsa-sage-waggle")

    # Check if SSH config file exists
    if os.path.exists(ssh_config):
        logging.info("SSH config file already exists. Skipping SSH setup.")
    else:
        logging.info("Setting up SSH config for nodes.")
        run_subprocess(["cp", "-r", SSH_TEMPLATE, ssh_dir])
        run_subprocess(["mkdir", "-p", os.path.join(ssh_dir, "master-socket")])
    
    # Start ssh-agent
    # TODO: figure out why ssh agent is not working in the script but in the container shell it is
    logging.info("Starting ssh-agent...")
    output = subprocess.check_output(["ssh-agent", "-s"], text=True)

    # Extract SSH_AUTH_SOCK and SSH_AGENT_PID using regex
    for line in output.splitlines():
        match = re.match(r'(\w+)=([^;]+);', line)
        if match:
            key, value = match.groups()
            os.environ[key] = value
            logging.info(f"Set env var: {key}={value}") #TODO: remove this later when you know it works

    # Add the key to the agent
    run_subprocess(["ssh-add", ssh_key_path], input_data=SSH_PWD + "\n")

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
    scrape_script = os.path.join(REPO_DIR, "scrape-nodes")
    input_data = "\n".join(vsns)
    try:
        run_subprocess(["xargs", "-n1", "-P4", scrape_script], input_data=input_data)
    except subprocess.CalledProcessError as e:
        logging.info(f"Error running scrape-nodes: {e}")

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

    # Step 1: Set up SSH config
    set_ssh()
    
    # Step 2: Get repo
    get_repo()
    
    # Step 3: Get vsns
    # vsns = get_vsns() TODO: Uncomment this line to get all vsns from the database
    vsns = ["W08E"] # NOTE: for development, I will only load the W08E node
    
    # Step 4: Scrape nodes
    scrape_nodes(vsns) #TODO: add the ssh config for our nodes so it can ssh into them
    
    # Step 5: Load manifests
    load_manifests(vsns)
    
    logging.info("Manifest loading process completed.")

#Cant use `if __name__ == "__main__":` because it is ran as an input to `django manage.py shell` command
main() 

# --- 10) Add to cron ---
# Cron job setup should be handled outside this script, for example:
# */30 * * * * /usr/bin/env python3 /app/scripts/load_manifest.py >> /var/log/load_manifest.log 2>&1

# NOTE: 
# - The scraped node data will go into the directory /app/waggle-inventory-tools/data/<vsn>/. 
# /app/waggle-inventory-tools/data will be an attached volume to systems' /etc/waggle/manifest so users can access it outside of the container/pod.