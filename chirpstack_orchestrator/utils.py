"""
Utility functions for ChirpStack orchestrator.
"""
from app.models import Node
from chirpstack_api_wrapper import ChirpstackClient
from django.conf import settings
from google.protobuf.json_format import MessageToDict

def get_chirpstack_client(vsn: str, email: str = settings.CHIRPSTACK_EMAIL, password: str = settings.CHIRPSTACK_PASSWORD, port: int = settings.CHIRPSTACK_PORT) -> ChirpstackClient:
    """
    Get a ChirpStack client for the given node vsn.
    Args:
        vsn (str): The vsn of the node.
        email (str): The email for authentication. Defaults to CHIRPSTACK_EMAIL configured in settings.
        password (str): The password for authentication. Defaults to CHIRPSTACK_PASSWORD configured in settings.
        port (int): The port for the ChirpStack API. Defaults to CHIRPSTACK_PORT configured in settings.
    Returns:
        ChirpstackClient: An instance of the ChirpStack client.
    """
    node = Node.objects.get(vsn=vsn)
    vpn_ip = node.vpn_ip.split("/")[0]
    return ChirpstackClient(
        email=email,
        password=password,
        api_endpoint=f"{vpn_ip}:{port}",
    )

def protos_to_dicts(protos: list) -> list:
    """
    Convert a list of protobuf messages to a list of dictionaries.
    Args:
        protos (list): A list of protobuf messages.
    Returns:
        list: A list of dictionaries.
    """
    return [MessageToDict(p, preserving_proto_field_name=True) for p in protos]

def proto_to_dict(proto) -> dict:
    """
    Convert a single protobuf message to a dictionary.
    Args:
        proto: A protobuf message.
    Returns:
        dict: A dictionary representation of the protobuf message.
    """
    return MessageToDict(proto, preserving_proto_field_name=True)