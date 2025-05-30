"""Custom Django command to Automatically load manifest data using data scraped from nodes into the database."""
import os
import subprocess
import re
from environ import Env
from manifests.management.commands.loadmanifest import Command as LoadManifestCommand

class Command(LoadManifestCommand):
    help = """
    Automatically Load manifest data using data scraped from nodes into the database. This builds off of 
    the loadmanifest command but sets up SSH and scraping tools for nodes.
    """
    env = Env()

    def handle(self, *args, **options):
        """
        Handle the command execution.
        """
        # Check if required options are set
        if not self.check_required_options(options):
            return
        self.set_constants(options)

        # Check if SSH directories exist
        if not self.check_ssh_dirs():
            return

        self.log("Starting manifest loading process...")
        # os.chdir(self.WORKDIR)

        # Set up SSH and clone the repo
        self.set_ssh()
        self.get_repo(options)

        # Get the list of VSNs to scrape/load
        vsns = self.get_vsns(options)
        self.scrape_nodes(vsns)
        self.load_manifests(vsns)

        self.log("Manifest loading process completed.")

    def add_arguments(self, parser):
        """
        Add command line arguments for the command.
        """
        parser.add_argument("--repo", type=str, default=self.env("INV_TOOLS_REPO", str, None), help="Inventory Tools Repository URL or local path")
        parser.add_argument("--token", type=str, default=self.env("INV_TOOLS_TOKEN", str, None), help="Github Token with access to INV_TOOLS_REPO URL")
        parser.add_argument("--repo_ver", type=str, default=self.env("INV_TOOLS_VERSION", str, None), help="Branch, tag, or commit SHA of INV_TOOLS_REPO URL to use")
        parser.add_argument("--ssh-tools", type=str, default=self.env("INV_TOOLS_SSH_TOOLS", str, None), help="Directory holding SSH tools used for SSHing into nodes")
        parser.add_argument("--ssh-config", type=str, default=self.env("INV_TOOLS_SSH_CONFIG", str, None), help="SSH directory holding config files")
        parser.add_argument("--ssh-pw", type=str, default=self.env("INV_TOOLS_SSH_TOOLS_PW", str, None), help="Password for SSH IdentityFile")
        parser.add_argument("--vsns", nargs="+", type=str, default=None, help="Optional list of VSNs to scrape/load. If not provided, all from DB will be used.")

    def check_required_options(self, options, required=None):
        """
        Check if required options are set. If not, log a message and return False.
        """
        if required is None:
            required = {
                "repo": "INV_TOOLS_REPO",
                "ssh_tools": "INV_TOOLS_SSH_TOOLS",
                "ssh_config": "INV_TOOLS_SSH_CONFIG",
                "ssh_pw": "INV_TOOLS_SSH_TOOLS_PW",
            }
        for opt_key, setting_name in required.items():
            if not options.get(opt_key):
                self.log(f"{setting_name} is not set (add arg --{opt_key} or env variable {setting_name}). Manifest loading will fail.")
                return False
        return True

    def set_constants(self, options):
        """
        Set constants for the Command.
        """
        self.WORKDIR = "/app"
        self.REPO = options["repo"]
        self.REPO_VERSION = options["repo_ver"]
        self.REPO_TOKEN = options["token"]
        self.SSH_PWD = options["ssh_pw"]
        self.SSH_TOOLS_DIR = options["ssh_tools"]
        self.SSH_TEMPLATE = options["ssh_config"]
        self.REPO_DIR = os.path.join(self.WORKDIR, "waggle-inventory-tools")
        self.DATA_DIR = os.path.join(self.REPO_DIR, "data")
        self.SSH_CONFIG_TEMPLATE = os.path.join(self.SSH_TEMPLATE, "config")
        self.HONEYHOUSE_DIR = os.path.join(self.SSH_TOOLS_DIR, "honeyhouse-config")
        self.PRIV_CONFIG_DIR = os.path.join(self.SSH_TOOLS_DIR, "private_config")
        self.DEVOPS_DIR = os.path.join(self.SSH_TOOLS_DIR, "devOps")

    def check_ssh_dirs(self):
        """
        Check if the SSH directories and files exist.
        """
        paths = [self.SSH_TEMPLATE, self.SSH_CONFIG_TEMPLATE, self.HONEYHOUSE_DIR, self.PRIV_CONFIG_DIR, self.DEVOPS_DIR]
        for path in paths:
            if not os.path.exists(path):
                self.log(f"{path} does not exist. Manifest loading will not proceed.")
                return False
        return True

    def is_commit_sha(self, ref):
        """Return True if ref looks like a git commit SHA."""
        return len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref.lower())

    def get_repo(self, options):
        """
        Clone the inventory tools repository if it doesn't exist, or use the cached one.
        Then checkout the specified version (branch, tag, or commit SHA).
        """
        if os.path.exists(self.REPO):  # Local repo directory
            self.log(f"Using local repo directory: {self.REPO}")
            self.REPO_DIR = self.REPO  # Override default REPO_DIR
        else:
            # Check if required options are set for remote repo
            required = {"repo": "INV_TOOLS_REPO", "token": "INV_TOOLS_TOKEN",}
            if not self.check_required_options(options, required):
                return
            # Remote repo URL (e.g., https://...)
            auth_repo_url = self.REPO.replace("https://", f"https://{self.REPO_TOKEN}@")
            if not os.path.exists(self.REPO_DIR):
                self.log(f"Cloning repo from {self.REPO} to {self.REPO_DIR}")
                self.run_subprocess(["git", "clone", auth_repo_url, self.REPO_DIR])
            else:
                self.log(f"Using cached repo at {self.REPO_DIR}")

            # Ensure Git knows it's safe to operate here
            self.run_subprocess(["git", "config", "--global", "--add", "safe.directory", self.REPO_DIR])
            self.run_subprocess(["git", "-C", self.REPO_DIR, "fetch", "--all", "--tags"])

            # Checkout branch/tag/commit
            if not self.REPO_VERSION:
                self.log("Checking out latest from main branch.")
                self.run_subprocess(["git", "-C", self.REPO_DIR, "checkout", "main"])
                self.run_subprocess(["git", "-C", self.REPO_DIR, "pull", "origin", "main"])
            else:
                self.log(f"Checking out version: {self.REPO_VERSION}")
                self.run_subprocess(["git", "-C", self.REPO_DIR, "fetch", "--all", "--tags"])
                if self.is_commit_sha(self.REPO_VERSION):
                    # It's a commit SHA
                    self.run_subprocess(["git", "-C", self.REPO_DIR, "checkout", self.REPO_VERSION])
                else:
                    # Check if the version is a branch or tag
                    result = subprocess.run(
                        ["git", "-C", self.REPO_DIR, "rev-parse", "--verify", f"origin/{self.REPO_VERSION}"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    if result.returncode == 0:
                        # It's a branch
                        self.run_subprocess(["git", "-C", self.REPO_DIR, "checkout", self.REPO_VERSION])
                        self.run_subprocess(["git", "-C", self.REPO_DIR, "pull", "origin", self.REPO_VERSION])
                    else:
                        # It's a tag
                        self.run_subprocess(["git", "-C", self.REPO_DIR, "checkout", f"tags/{self.REPO_VERSION}"])

        # Set working directory to the repo
        os.chdir(self.REPO_DIR)

    def set_ssh(self):
        """
        Set up SSH configuration for the nodes.
        """
        ssh_dir = os.path.expanduser("~/.ssh")
        ssh_config = os.path.join(ssh_dir, "config")
        ssh_key_path = os.path.join(self.PRIV_CONFIG_DIR ,"misc/waggle-sage/ecdsa-sage-waggle")

        # Check if SSH config file exists
        if not os.path.exists(ssh_config):
            self.log("Setting up SSH config for nodes.")
            self.run_subprocess(["cp", "-r", self.SSH_TEMPLATE, ssh_dir])
            self.run_subprocess(["mkdir", "-p", os.path.join(ssh_dir, "master-socket")])

        # Start ssh-agent
        self.log("Starting ssh-agent...")
        output = subprocess.check_output(["ssh-agent", "-s"], text=True)

        # Extract SSH_AUTH_SOCK and SSH_AGENT_PID using regex
        for line in output.splitlines():
            match = re.match(r'(\w+)=([^;]+);', line)
            if match:
                key, value = match.groups()
                os.environ[key] = value

        # Add the key to the agent
        self.run_subprocess(["ssh-add", ssh_key_path], input_data=self.SSH_PWD + "\n")

# NOTE: 
# - The scraped node data will go into the directory /app/waggle-inventory-tools/data/<vsn>/. 
# /app/waggle-inventory-tools/data will be an attached volume to systems' /etc/waggle/manifest so users can access it outside of the container/pod.