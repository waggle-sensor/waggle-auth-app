from manifests.models import *
import csv


with open("scripts/data/hardware.csv") as file:
    reader = csv.DictReader(file)

    ComputeHardware.objects.all().delete()
    SensorHardware.objects.all().delete()
    ResourceHardware.objects.all().delete()
    Capability.objects.all().delete()

    for row in reader:
        print(row)

        if row["hardware_type"] == "compute":
            hardware = ComputeHardware.objects.create(
                hardware=row["hardware"].strip(),
                hw_model=row["hw_model"].strip(),
                hw_version=row["hw_version"].strip(),
                manufacturer=row["manufacturer"].strip(),
                datasheet=row["datasheet"].strip(),
                cpu=row["cpu"].strip(),
                cpu_ram=row["cpu_ram"].strip(),
                gpu_ram=row["gpu_ram"].strip(),
                shared_ram=bool(row["shared_ram"].strip()),
            )

        elif row["hardware_type"] == "sensor":
            hardware = SensorHardware.objects.create(
                hardware=row["hardware"].strip(),
                hw_model=row["hw_model"].strip(),
                hw_version=row["hw_version"].strip(),
                manufacturer=row["manufacturer"].strip(),
                datasheet=row["datasheet"].strip(),
            )

        # hardware_type == resource
        else:
            hardware = ResourceHardware.objects.create(
                hardware=row["hardware"].strip(),
                hw_model=row["hw_model"].strip(),
                hw_version=row["hw_version"].strip(),
                manufacturer=row["manufacturer"].strip(),
                datasheet=row["datasheet"].strip(),
            )

        # Create Capabilitiy object only if hardware.csv/capabilities column has value and the val does not exist in current Capability model
        if len(row["capabilities"].strip()) > 0:
            for c in row["capabilities"].split(","):
                c = c.strip()
                capability, _ = Capability.objects.get_or_create(capability=c)
                hardware.capabilities.add(capability)
