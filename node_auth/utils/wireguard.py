"""
WireGuard utility functions for managing VPN IP allocation and peer creation/deletion.
"""
import ipaddress
import logging
import subprocess
import shutil
import json
from app.models import Token
from django.conf import settings
from app.models import Node
from pyroute2 import IPRoute

logger = logging.getLogger(__name__)

def allocate_next_ip(node: Node, subnet: str = "10.0.0.0/24") -> str:
    """
    Allocates a /32 VPN IP for the given node.
    Reuses existing IP if valid; otherwise finds a new one.
    """
    network = ipaddress.ip_network(subnet)

    # Reuse existing valid IP if already assigned
    if node.vpn_ip:
        try:
            existing_ip = ipaddress.ip_interface(node.vpn_ip)
            if existing_ip.ip in network:
                return node.vpn_ip
        except ValueError:
            logger.warning(f"[WIREGUARD] allocate_next_ip(): Invalid existing VPN IP for node {node.pk}: {node.vpn_ip}")
            pass  # continue with allocation

    # Set to collect used IPs
    used_ips = set()

    # Collect VPN IPs from the DB
    for other in Node.objects.exclude(vpn_ip__isnull=True).exclude(pk=node.pk):
        try:
            ip = ipaddress.ip_interface(other.vpn_ip).ip
            used_ips.add(ip)
        except ValueError:
            logger.warning(f"[WIREGUARD] allocate_next_ip(): Invalid VPN IP for node {other.pk}: {other.vpn_ip}")
            continue

    # Collect VPN IPs from running WireGuard config
    try:
        ipr = IPRoute()
        idx = ipr.link_lookup(ifname=settings.WG_IFACE)[0]
        info = ipr.get_links(idx)[0].get_attr('IFLA_LINKINFO')
        peers = info.get('data', {}).get('peers', [])
        for peer in peers:
            allowed_ips = peer.get('allowed_ips', [])
            for ip_int, _ in allowed_ips:
                ip = ipaddress.ip_address(ip_int)
                used_ips.add(ip)
    except Exception as e:
        logger.warning(f"[WIREGUARD] Warning reading live peers: {e}")
    finally:
        ipr.close()

    # Find first available IP
    for ip in network.hosts():
        if ip in used_ips:
            continue
        return f"{ip}/32"

    logger.error(
        f"[WIREGUARD] ERROR: No available VPN IPs in the subnet {subnet} for node {node.pk}."
    )
    return None

def wg_enabled():
    """
    Check if WireGuard is enabled in settings and if the `wg` command is available.
    """
    if not settings.WG_ENABLED:
        logger.info("[WIREGUARD] wg_enabled(): WireGuard is not enabled in settings.")
        return False
    if shutil.which("wg") is None:
        logger.info("[WIREGUARD] wg_enabled(): 'wg' command is not available so WireGuard will be disabled.")
        return False
    return True

def get_interface_ip(iface):
    """
    Get the IP address of the server's network interface.
    """
    try:
        result = subprocess.run(
            ["ip", "-j", "addr", "show", "dev", iface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        data = json.loads(result.stdout)
        for addr_info in data[0].get("addr_info", []):
            if addr_info.get("family") == "inet":
                return addr_info.get("local")  # e.g., "10.0.0.1"
    except Exception as e:
        logger.error(f"[WIREGUARD] get_interface_ip(): Failed to get IP for {iface}: {e}")

def gen_keys():
    """
    Generate a WireGuard private and public key pair.
    
    Returns:
        (private_key, public_key): Tuple of base64-encoded keys as strings.
    """
    # Generate private key
    priv_proc = subprocess.run(
        ["wg", "genkey"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    priv_key = priv_proc.stdout.decode().strip()

    # Derive public key
    pub_proc = subprocess.run(
        ["wg", "pubkey"],
        input=priv_key.encode(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    pub_key = pub_proc.stdout.decode().strip()

    return priv_key, pub_key

def create_peer(token_id):
    """
    Create a WireGuard peer for the given token ID.

    Returns:
        bool: True if peer was successfully created, False otherwise.
    """
    if not wg_enabled():
        return False
    try:
        token = Token.objects.select_related('node').get(pk=token_id)
    except Token.DoesNotExist:
        logger.error(f"[WIREGUARD] create_peer(): Token {token_id} does not exist.")
        return False
    except Exception as e:
        logger.error(f"[WIREGUARD] create_peer(): Error fetching token {token_id}: {e}")
        return False

    # Allocate or reuse VPN IP
    vpn_ip = allocate_next_ip(token.node, subnet=settings.WG_NETWORK)
    if vpn_ip != token.node.vpn_ip:
        token.node.vpn_ip = vpn_ip
        token.node.save(update_fields=["vpn_ip"])

    # Prepare peer definition
    pubkey = token.wg_pub_key
    if not pubkey or not vpn_ip:
        logger.error(f"[WIREGUARD] create_peer(): Missing pubkey or VPN IP for token {token.pk}")
        return False

    try:
        subprocess.run([
            "wg", "set", settings.WG_IFACE,
            "peer", pubkey.strip(),
            "allowed-ips", vpn_ip,
            "persistent-keepalive", "25"
        ], check=True)
        logger.info(f"[WIREGUARD] create_peer(): Added peer {pubkey} with IP {vpn_ip}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[WIREGUARD] create_peer(): Failed to add peer {token.pk}: {e}")
        return False

    return True

def delete_peer(token_id):
    """
    Remove a WireGuard peer from the server config and release its VPN IP.

    Returns:
        bool: True if peer was successfully deleted, False otherwise.
    """
    if not wg_enabled():
        return False
    try:
        token = Token.objects.select_related('node').get(pk=token_id)
    except Token.DoesNotExist:
        logger.error(f"[WIREGUARD] delete_peer(): Token {token_id} does not exist.")
        return False

    # Remove the peer from WireGuard config
    pubkey = token.wg_pub_key
    if not pubkey:
        logger.error(f"[WIREGUARD] delete_peer(): Missing pubkey for token {token.pk}")
        return False

    try:
        subprocess.run([
            "wg", "set", settings.WG_IFACE,
            "peer", pubkey.strip(),
            "remove"
        ], check=True)
        logger.info(f"[WIREGUARD] delete_peer(): Removed peer {pubkey.strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[WIREGUARD] delete_peer(): Failed to remove peer {token.pk}: {e}")
        return False

    try:
        token.node.vpn_ip = None
        token.node.save(update_fields=["vpn_ip"])
    except Exception as e:
        logger.info(f"[WIREGUARD] delete_peer(): Could not release IP for node {token.node.pk} in db: {e}")

    return True
