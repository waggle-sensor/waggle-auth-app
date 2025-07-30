"""
WireGuard utility functions for managing VPN IP allocation and peer creation/deletion.
"""
import ipaddress
import base64
import logging
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
            if existing_ip.ip in network and existing_ip.ip not in settings.WG_RESERVED_IPS:
                return node.vpn_ip
        except ValueError:
            pass  # continue with allocation

    # Set to collect used IPs
    used_ips = set()

    # Collect VPN IPs from the DB
    for other in Node.objects.exclude(vpn_ip__isnull=True).exclude(pk=node.pk):
        try:
            ip = ipaddress.ip_interface(other.vpn_ip).ip
            used_ips.add(ip)
        except ValueError:
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

    # Reserved IPs
    reserved_ips = {ipaddress.ip_address(ip) for ip in settings.WG_RESERVED_IPS}

    # Find first available IP
    for ip in network.hosts():
        if ip in used_ips or ip in reserved_ips:
            continue
        return f"{ip}/32"

    logger.error(
        f"[WIREGUARD] ERROR: No available VPN IPs in the subnet {subnet} for node {node.pk}."
    )
    return None

def create_peer(token_id):
    """
    Create a WireGuard peer for the given token ID.
    """
    # Retrieve the token and its associated node
    try:
        token = Token.objects.select_related('node').get(pk=token_id)
    except Token.DoesNotExist:
        return

    # Allocate or reuse VPN IP
    vpn_ip = allocate_next_ip(token.node, subnet=settings.WG_NETWORK)
    if vpn_ip != token.node.vpn_ip:
        token.node.vpn_ip = vpn_ip
        token.node.save(update_fields=["vpn_ip"])

    # Prepare peer definition
    pubkey = token.wg_pub_key
    try:
        ipr = IPRoute()
        idx = ipr.link_lookup(ifname=settings.WG_IFACE)[0]

        interface = ipaddress.ip_interface(vpn_ip)
        ipr.link('set',
                 index=idx,
                 kind='wireguard',
                 wireguard_peers=[{
                     'public_key': base64.b64decode(pubkey),
                     'allowed_ips': [(str(interface.ip), interface.network.prefixlen)],
                     'persistent_keepalive': 25,
                 }])
    finally:
        ipr.close()

def delete_peer(token_id):
    """
    Remove a WireGuard peer from the server config and release its VPN IP.
    """
    # Retrieve the token and its associated node
    try:
        token = Token.objects.select_related('node').get(pk=token_id)
    except Token.DoesNotExist:
        return

    # Remove the peer from WireGuard config
    pubkey = token.wg_pub_key
    try:
        ipr = IPRoute()
        idx = ipr.link_lookup(ifname=settings.WG_IFACE)[0]
        ipr.link('set',
                 index=idx,
                 kind='wireguard',
                 wireguard_peers=[{
                     'public_key': base64.b64decode(pubkey),
                     'remove': True
                 }])
    finally:
        ipr.close()

    # Optionally release the IP
    try:
        token.node.vpn_ip = None
        token.node.save(update_fields=["vpn_ip"])
    except Exception as e:
        logger.info(f"[WIREGUARD] INFO: releasing VPN IP for node {token.node.pk} failed: {e}")
