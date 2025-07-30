import base64
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from pyroute2 import IPRoute
from pyroute2.netlink.rtnl.ifinfmsg import IFF_UP
from app.models import Token
import ipaddress

class Command(BaseCommand):
    help = "Set up WireGuard interface and reattach all peers from the Token model."

    def log(self, message):
        """
        Log messages.
        """
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.stdout.write(f"{timestamp} [WIREGUARD]: {message}")
    
    def add_arguments(self, parser):
        parser.add_argument('--iface', 
                            type=str, 
                            help='WireGuard interface name (default from settings)',
                            default=settings.WG_IFACE)
        parser.add_argument('--priv-key', 
                            type=str, 
                            help='Server\'s Base64-encoded private key (default from settings)',
                            default=settings.WG_PRIV_KEY)
        parser.add_argument('--pub-key', 
                            type=str, 
                            help='Server\'s Base64-encoded public key (default from settings)',
                            default=settings.WG_PUB_KEY)
        parser.add_argument('--server-addr', 
                            type=str, 
                            help='Server IP/CIDR (default from settings)',
                            default=settings.WG_SERVER_ADDRESS)
        parser.add_argument('--port', 
                            type=int, 
                            help='Listen port (default from settings)',
                            default=settings.WG_PORT)

    def handle(self, *args, **options):
        iface = options['iface']
        priv_key_b64 = options['priv_key']
        pub_key_b64 = options['pub_key']
        server_addr = options['server_addr']
        listen_port = options['port']

        ipr = IPRoute()

        try:
            # Create interface if missing
            links = ipr.link_lookup(ifname=iface)
            if not links:
                self.log(f"Creating interface {iface}...")
                ipr.link("add", ifname=iface, kind="wireguard")
            idx = ipr.link_lookup(ifname=iface)[0]

            # Set private key and port
            ipr.link("set",
                index=idx,
                kind="wireguard",
                wireguard_private_key=base64.b64decode(priv_key_b64),
                wireguard_listen_port=listen_port,
            )

            # Assign address if missing
            addr, prefixlen = server_addr.split("/")
            prefixlen = int(prefixlen)
            assigned = [
                a.get_attr("IFA_ADDRESS")
                for a in ipr.get_addr(index=idx)
                if a.get_attr("IFA_ADDRESS") is not None
            ]
            if addr not in assigned:
                self.log(f"Assigning IP {server_addr} to server...")
                ipr.addr("add", index=idx, address=addr, mask=prefixlen)

            # Bring up the interface
            ipr.link("set", index=idx, state="up", flags=IFF_UP)
            self.log(f"{iface} is up at {server_addr}:{listen_port}")

            # Reattach all peers from the Token model
            tokens = Token.objects.select_related("node").exclude(wg_pub_key__isnull=True, node__vpn_ip__isnull=True)
            added = 0
            peer_configs = []
            for token in tokens:
                pub_key = token.wg_pub_key
                vpn_ip = token.node.vpn_ip
                if not pub_key or not vpn_ip:
                    continue
                try:
                    interface = ipaddress.ip_interface(vpn_ip)
                    peer_configs.append({
                        'public_key': base64.b64decode(pub_key),
                        'allowed_ips': [(str(interface.ip), interface.network.prefixlen)],
                        'persistent_keepalive': 25,
                    })
                    added += 1
                except Exception as e:
                    self.log(f"Failed to add peer for node {token.node_id}: {e}")

            try:
                if peer_configs:
                    ipr.link("set",
                        index=idx,
                        kind="wireguard",
                        wireguard_peers=peer_configs
                    )
            except Exception as e:
                self.log(f"Failed to set peers for {iface}: {e}")

            self.log(f"Added {added} peer(s) to {iface}")

            # Set the server's public key in settings
            settings.WG_PUB_KEY = pub_key_b64
            self.log(f"Server Public key: {pub_key_b64}")

        except Exception as e:
            self.log(f"WireGuard setup failed: {e}")
        finally:
            ipr.close()
