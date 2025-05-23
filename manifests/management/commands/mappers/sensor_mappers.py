from manifests.models import ComputeSensor

COMPUTE_SENSOR_MAPPERS = [
    {
        "source": "iio_devices",
        "sensor_names": lambda dev: dev.get("iio_devices", []),
        "resolve_hardware": lambda name: ComputeSensor._meta.get_field("hardware").related_model.objects.filter(hardware=name).first(),
    },
    {
        "source": "lora_gws",
        "sensor_names": lambda dev: ["lorawan", "Lorawan Antenna"] if dev.get("lora_gws") else [],
        "resolve_hardware": lambda name: ComputeSensor._meta.get_field("hardware").related_model.objects.filter(
            hardware="lorawan" if "lorawan" in name.lower() else "LoRa Fiber Glass Antenna"
        ).first(),
    }
]