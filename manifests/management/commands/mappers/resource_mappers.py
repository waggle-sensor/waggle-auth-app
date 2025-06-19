from manifests.models import ResourceHardware

#NOTE: add your resource mappers here
RESOURCE_MAPPERS = [
    {
        "source": "waggle_devices",
        "resouce_names": lambda dev: ["switch"] if any(d.get("id") == "waggle-core-switchconsole" for d in dev.get("waggle_devices", [])) else [],
        "resolve_hardware": lambda name: ResourceHardware.objects.get_or_create(hardware=name)[0],
    },
]