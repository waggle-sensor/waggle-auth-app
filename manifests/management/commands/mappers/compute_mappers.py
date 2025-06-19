from manifests.models import ComputeHardware

# NOTE: add your compute mappers here
# example: "nxcore": {"pattern": "nxcore", "hardware": "xavieragx", "condition": lambda d: d.get("model", "") == "NVIDIA Jetson AGX Orin"},
COMPUTE_ALIAS_MAP = {
    "nxcore": {
        "pattern": "nxcore",
        "hardware": "xaviernx",
    },
    "sbcore": {
        "pattern": "sb-core",
        "hardware": "dell-xr2",
    },
    "nxagent": {
        "pattern": "nxagent",
        "hardware": "xaviernx-poe",
    },
    "rpi.lorawan": {
        "pattern": "ws-rpi",
        "condition": lambda d: bool(d.get("lora_gws")),
    },
    "rpi": {
        "pattern": "ws-rpi",
    },
    "custom": {
        "pattern": "custom",
        "hardware": "custom",
    },
}
DEFAULT_COMPUTE_ALIAS = "custom"


def Resolve_compute_alias(hostname, device):
    for alias, config in COMPUTE_ALIAS_MAP.items():
        if config["pattern"] in hostname and config.get("condition", lambda d: True)(
            device
        ):
            return alias
    return DEFAULT_COMPUTE_ALIAS


def Get_hardware_for_alias(alias, dev):
    hardware_name = COMPUTE_ALIAS_MAP.get(alias, {}).get("hardware")

    memory_gb = parse_memory(dev["k8s"]["resources"]["memory"]["capacity"]) / 1024**3

    if "Raspberry Pi" in dev["model"]:
        if memory_gb < 6:
            hardware_name = "rpi-4gb"
        else:
            hardware_name = "rpi-8gb"

    if hardware_name is None:
        raise ValueError("unable to determined hardware model")

    return ComputeHardware.objects.get_or_create(hardware=hardware_name)[0]


def parse_memory(s: str) -> int:
    """Parse string of memory with units suffix into interger memory in bytes."""
    if s.endswith("Ki"):
        return int(s.removesuffix("Ki")) * 1024
    raise ValueError(f"unsupported memory string {s}")
