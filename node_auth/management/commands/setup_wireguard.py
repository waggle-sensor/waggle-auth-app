from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import tempfile
import os
import ipaddress
from app.models import Token
from node_auth.utils import wireguard as wg

class Command(BaseCommand):
    help = """
    Set up WireGuard interface and reattach all peers from the Token model.

    Examples:
    python manage.py setup_wireguard
    python manage.py setup_wireguard --migrate
    python manage.py setup_wireguard --iface wg0 --port 51820 --wg-server-addr 10.0.0.1/22
    """

    def log(self, message):
        """
        Log messages.
        """
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.stdout.write(f"{timestamp} [WIREGUARD] setup_wireguard(): {message}")

    def run(self, cmd, check=True, **kwargs):
        """Run shell command and log output/errors."""
        try:
            subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e.cmd}\n{e.stderr.decode().strip()}")
            raise
    
    def add_arguments(self, parser):
        """
        Add command line arguments for WireGuard setup.
        """
        parser.add_argument('--iface', type=str, default=settings.WG_IFACE,
                            help='WireGuard interface name (default from settings)')
        parser.add_argument('--priv-key', type=str, default=settings.WG_PRIV_KEY,
                            help='Server\'s Base64-encoded private key (default from settings)')
        parser.add_argument('--pub-key', type=str, default=settings.WG_PUB_KEY,
                            help='Server\'s Base64-encoded public key (default from settings)')
        parser.add_argument('--wg-server-addr', type=str, default=settings.WG_SERVER_ADDRESS,
                            help='WireGuard server address using CIDR (default from settings)')
        parser.add_argument('--port', type=int, default=settings.WG_PORT,
                            help='Listen port (default from settings)')
        parser.add_argument('--migrate', action='store_true',
                            help='Generate missing WireGuard key pairs for Node tokens')

    def handle(self, *args, **options):
        """
        Handle the command to set up WireGuard.
        """
        if not wg.wg_enabled():
            return
        self.log("Starting WireGuard setup...")
        iface = options['iface']
        settings.WG_IFACE = iface
        priv_key_b64 = options['priv_key']
        settings.WG_PRIV_KEY = priv_key_b64
        pub_key_b64 = options['pub_key']
        settings.WG_PUB_KEY = pub_key_b64
        wg_server_addr = options['wg_server_addr']
        settings.WG_SERVER_ADDRESS = wg_server_addr
        settings.WG_NETWORK = ipaddress.ip_network(wg_server_addr, strict=False)
        listen_port = options['port']
        settings.WG_PORT = listen_port
        do_migrate = options['migrate']

        # If public IP is not set, fetch it
        if not settings.WG_PUBLIC_IP:
            self.log("Fetching public IP address for WireGuard server...")
            settings.WG_PUBLIC_IP = wg.get_public_ip()

        try:

            # Place private key in a temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_key_file:
                temp_key_file.write(priv_key_b64.strip())
                temp_key_file.flush()
                key_file_path = temp_key_file.name

            # Create WireGuard interface
            self.run(f"ip link add dev {iface} type wireguard", check=False)
            self.run(f"ip address add dev {iface} {wg_server_addr}")
            self.run(f"wg set {iface} private-key {key_file_path}")
            self.run(f"ip link set up dev {iface}")
            self.run(f"wg set {iface} listen-port {listen_port}")
            os.remove(key_file_path)

            # get server ip address
            server_addr = wg.get_interface_ip(iface)
            if server_addr:
                self.log(f"Server IP on {iface}: {server_addr}")
            else:
                self.log("Failed to determine server IP")
                return
            self.log(f"{iface} is up at {server_addr}:{listen_port}")
            settings.WG_SERVER_ADDRESS = server_addr

            # Optional migration
            if do_migrate:
                migrated = 0
                tokens = Token.objects.select_related("node").filter(wg_priv_key__isnull=True) | Token.objects.filter(wg_pub_key__isnull=True)
                self.log(f"Found {tokens.count()} Node Token(s) with missing keys, generating new keys...")
                for token in tokens:
                    priv, pub = wg.gen_keys()
                    token.wg_priv_key = priv
                    token.wg_pub_key = pub
                    token.save(update_fields=["wg_priv_key", "wg_pub_key"])
                    if wg.create_peer(token.key):
                        migrated += 1
                self.log(f"Migrated {migrated} Node Token(s) with missing keys")

            # Reattach peers
            added = 0
            tokens = Token.objects.select_related("node").exclude(wg_pub_key__isnull=True)
            self.log(f"Attempting to reattach {tokens.count()} peers to {iface}...")
            for token in tokens:
                if wg.create_peer(token.pk):
                    added += 1
            self.log(f"Added {added} peer(s) to {iface}")

            # Finalize setup
            self.log(f"""
                     WireGuard setup complete on {iface}: 
                     public_ip={settings.WG_PUBLIC_IP}, 
                     network={settings.WG_NETWORK}, 
                     server_address={settings.WG_SERVER_ADDRESS}, 
                     port={settings.WG_PORT}, 
                     public_key={settings.WG_PUB_KEY}
                    """)

        except Exception as e:
            self.log(f"WireGuard setup failed: {e}")
