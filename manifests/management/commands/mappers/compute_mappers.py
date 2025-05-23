from manifests.models import ComputeHardware

COMPUTE_ALIAS_MAP = {
    "nxcore": {"pattern": "nxcore", "hardware": "xaviernx"},
    "sbcore": {"pattern": "sb-core", "hardware": "dell-xr2"},
    "nxagent": {"pattern": "nxagent", "hardware": "xaviernx-poe"},
    "rpi.lorawan": {"pattern": "ws-rpi", "hardware": "rpi-4gb", "condition": lambda d: bool(d.get("lora_gws"))},
    "rpi": {"pattern": "ws-rpi", "hardware": "rpi-8gb"},
    "custom": {"pattern": "custom", "hardware": "custom"},
}
DEFAULT_COMPUTE_ALIAS = "custom"

def Resolve_compute_alias(hostname, device):
    for alias, config in COMPUTE_ALIAS_MAP.items():
        if config["pattern"] in hostname and config.get("condition", lambda d: True)(device):
            return alias
    return DEFAULT_COMPUTE_ALIAS

def Get_hardware_for_alias(alias):
    hardware_name = COMPUTE_ALIAS_MAP.get(alias, {}).get("hardware")
    return ComputeHardware.objects.get_or_create(hardware=hardware_name)[0]