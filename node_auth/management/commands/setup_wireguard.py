from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import tempfile
import os
import ipaddress
import time
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

    def is_wireguard_go_running(self, iface):
        """Check if wireguard-go is running for the specified interface."""
        try:
            out = subprocess.check_output(['pgrep', '-af', 'wireguard-go']).decode()
            for line in out.strip().split('\n'):
                if f"wireguard-go {iface}" in line:
                    return int(line.split()[0])  # Return PID
        except subprocess.CalledProcessError:
            pass
        return None

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
        parser.add_argument('--wg-server-addr-cidr', type=str, default=settings.WG_SERVER_ADDRESS_WITH_CIDR,
                            help='WireGuard server address using CIDR (default from settings)')
        parser.add_argument('--port', type=int, default=settings.WG_PORT,
                            help='Listen port (default from settings)')
        parser.add_argument('--migrate', action='store_true',
                            help='Generate missing WireGuard key pairs for Node tokens')
        parser.add_argument('--restart', action='store_true',
                            help='Restart wireguard-go if it is already running')

    def handle(self, *args, **options):
        """
        Handle the command to set up WireGuard.
        """
        if not wg.wg_enabled():
            return

        self.log("Starting WireGuard setup...")

        iface = options['iface']
        priv_key_b64 = options['priv_key']
        pub_key_b64 = options['pub_key']
        wg_server_addr_with_cidr = options['wg_server_addr_cidr']
        wg_network = str(ipaddress.ip_network(wg_server_addr_with_cidr, strict=False))
        listen_port = options['port']
        do_migrate = options['migrate']
        do_restart = options['restart']
        wg_pub_ip = wg.get_public_ip()

        try:
            # Kill existing wireguard-go if running and --restart specified
            existing_pid = self.is_wireguard_go_running(iface)
            if existing_pid:
                if do_restart:
                    self.log(f"wireguard-go already running for {iface} (pid={existing_pid}), restarting...")
                    try:
                        os.kill(existing_pid, 15)
                        time.sleep(1)
                    except Exception as e:
                        self.log(f"Failed to terminate existing wireguard-go process: {e}")
                else:
                    self.log(f"wireguard-go already running for {iface} (pid={existing_pid}), skipping restart.")
                    return

            # Start wireguard-go
            self.log(f"Launching wireguard-go for {iface}...")
            subprocess.Popen(["wireguard-go", iface])
            time.sleep(10)  # Wait for wireguard-go to initialize

            # Write private key to temp file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_key_file:
                temp_key_file.write(priv_key_b64.strip())
                temp_key_file.flush()
                key_file_path = temp_key_file.name

            # Interface setup
            self.run(f"ip address add {wg_server_addr_with_cidr} dev {iface} ")
            self.run(f"wg set {iface} private-key {key_file_path}")
            self.run(f"ip link set up dev {iface}")
            self.run(f"wg set {iface} listen-port {listen_port}")
            os.remove(key_file_path)

            # get server ip address
            wg_server_addr = wg.get_interface_ip(iface)
            if wg_server_addr:
                self.log(f"Server IP on {iface}: {wg_server_addr}")
            else:
                self.log("Failed to determine server IP")
                return
            self.log(f"{iface} is up at {wg_server_addr}:{listen_port}")

            # Optional migration
            if do_migrate:
                self.log("Migrating Node Tokens with missing WireGuard keys...")
                migrated = 0
                tokens = Token.objects.select_related("node").filter(wg_priv_key__isnull=True) | Token.objects.filter(wg_pub_key__isnull=True)
                self.log(f"Found {tokens.count()} Node Token(s) with missing keys")
                for token in tokens:
                    priv, pub = wg.gen_keys()
                    token.wg_priv_key = priv
                    token.wg_pub_key = pub
                    token.save(update_fields=["wg_priv_key", "wg_pub_key"])
                    if wg.create_peer(token.key, wg_network=wg_network, wg_iface=iface):
                        migrated += 1
                self.log(f"Migrated {migrated} Node Token(s) with missing keys")

            # Reattach peers
            added = 0
            tokens = Token.objects.select_related("node").exclude(wg_pub_key__isnull=True)
            self.log(f"Attempting to reattach {tokens.count()} peers to {iface}...")
            for token in tokens:
                if wg.create_peer(token.pk, wg_network=wg_network, wg_iface=iface):
                    added += 1
            self.log(f"Added {added} peer(s) to {iface}")

            # Finalize setup
            self.log(f"""WireGuard setup complete on {iface} 
                     - public_ip={wg_pub_ip}
                     - network={wg_network}
                     - server_address={wg_server_addr}
                     - port={str(listen_port)}
                     - public_key={pub_key_b64}
                    """)
            
            # Save environment variables
            wg.save_env_vars({
                "WG_IFACE": iface,
                "WG_PRIV_KEY": priv_key_b64,
                "WG_PUB_KEY": pub_key_b64,
                "WG_SERVER_ADDRESS": wg_server_addr,
                "WG_SERVER_ADDRESS_WITH_CIDR": wg_server_addr_with_cidr,
                "WG_PORT": str(listen_port),
                "WG_PUBLIC_IP": wg_pub_ip,
                "WG_NETWORK": wg_network,
            }, filepath=settings.WG_VAR_FILE)

        except Exception as e:
            self.log(f"WireGuard setup failed: {e}")
