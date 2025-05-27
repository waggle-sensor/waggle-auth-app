from manifests.models import SensorHardware

#NOTE: add your sensor mappers here
COMPUTE_SENSOR_MAPPERS = [
    {
        "source": "iio_devices",
        "sensor_names": lambda dev: dev.get("iio_devices", []),
        "resolve_hardware": lambda name: SensorHardware.objects.get_or_create(hardware=name)[0],
    },
    {
        "source": "lora_gws",
        "sensor_names": lambda dev: ["lorawan", "Lorawan Antenna"] if dev.get("lora_gws") else [],
        "resolve_hardware": lambda name: SensorHardware.objects.get_or_create(
            hardware="lorawan" if "lorawan" in name.lower() else "LoRa Fiber Glass Antenna"
        )[0],
    },
    {
        "source": "waggle_devices",
        "sensor_names": lambda dev: ["gps"] if any(d.get("id") == "waggle-core-gps" for d in dev.get("waggle_devices", [])) else [],
        "resolve_hardware": lambda name: SensorHardware.objects.get_or_create(hardware=name)[0],
    },
    {
        "source": "k8s",
        "sensor_names": lambda dev: [
            name for name in ["raingauge", "microphone"]
            if dev.get("k8s", {}).get("labels", {}).get(f"resource.{name}", "") == "true"
        ],
        "resolve_hardware": lambda name: SensorHardware.objects.get_or_create(
            hardware=name.lower()
        )[0],
    }
]