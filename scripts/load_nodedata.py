from manifests.models import *
import csv


def infer_camera_hardware_from_name(name):
    if name == "True PTZ (XNP-6400RW)":
        return SensorHardware.objects.get(hardware="ptz-6400")
    if name == "Thermal (mobotix)":
        return SensorHardware.objects.get(hardware="mobotix-m16")
    camera_type = name.split()[0].lower()
    number = name.split("-")[1][:4]
    hardware = camera_type + "-" + number
    return SensorHardware.objects.get(hardware=hardware)


with open('scripts/data/nodedata.csv') as file:
    reader = csv.DictReader(file)

    # skip the data type row
    next(reader)

    NodeData.objects.all().delete()
    Compute.objects.all().delete()
    ComputeSensor.objects.all().delete()
    NodeSensor.objects.all().delete()
    Resource.objects.all().delete()

    for row in reader:
        print(row)

        n = NodeData.objects.create(
            vsn=row["vsn"].strip().upper(),
            name=row["node_id"].strip().upper(),
            gps_lat=float(row["gps_lat"].strip() or 0),
            gps_lon=float(row["gps_lon"].strip() or 0),
        )

        # add below hardwares to every node:
        # 1. xaviernx
        nx = ComputeHardware.objects.get(hardware="xaviernx")
        n.computes.add(nx)
        Compute.objects.filter(node=n, hardware=nx).update(zone="core")
        Compute.objects.filter(node=n, hardware=nx).update(serial_no=row["node_id"][4:])

        # 2. bme280
        # 3. gps
        compute = Compute.objects.get(node=n, hardware=nx)
        ComputeSensor.objects.create(scope=compute, hardware=SensorHardware.objects.get(hardware="bme280"))
        NodeSensor.objects.create(node=n, hardware=SensorHardware.objects.get(hardware="gps"))

        # 4. usbhub-10port
        # 5. wagman
        Resource.objects.create(node=n, hardware=ResourceHardware.objects.get(hardware="usbhub-10port"))
        Resource.objects.create(node=n, hardware=ResourceHardware.objects.get(hardware="wagman"))

        # 6. psu: psu-B0BD for nodes before (but not include) W040, psu-BBBD for nodes after W040
        # 7. wifi: for nodes after W040
        if row["flag"] == "group1":
            Resource.objects.create(node=n, hardware=ResourceHardware.objects.get(hardware="psu-b0bd"))
        else:
            Resource.objects.create(node=n, hardware=ResourceHardware.objects.get(hardware="psu-bbbd"))
            Resource.objects.create(node=n, hardware=ResourceHardware.objects.get(hardware="wifi"))

        # infer cameras
        for camera in ["top_camera", "bottom_camera", "left_camera", "right_camera"]:
            if row[camera] == "none":
                continue
            hardware = infer_camera_hardware_from_name(row[camera].strip())
            NodeSensor.objects.create(node=n, hardware=SensorHardware.objects.get(hardware=hardware))

        # nx_agent
        if row["nx_agent"] == "yes":
            poe = ComputeHardware.objects.get(hardware="xaviernx-poe")
            n.computes.add(poe)
            Compute.objects.filter(node=n, hardware=poe).update(zone="agent")

        # shield
        if row["shield"] == "yes":
            if row["flag"] == "group1":
                rpi4 = ComputeHardware.objects.get(hardware="rpi-4gb")
                c1 = Compute.objects.create(node=n, hardware=rpi4)
                Compute.objects.filter(node=n, hardware=rpi4).update(zone="shield")

                ComputeSensor.objects.create(scope=c1, hardware=SensorHardware.objects.get(hardware="bme680"))
                ComputeSensor.objects.create(scope=c1, hardware=SensorHardware.objects.get(hardware="microphone"))
                ComputeSensor.objects.create(scope=c1, hardware=SensorHardware.objects.get(hardware="rainguage"))
            else:
                rpi8 = ComputeHardware.objects.get(hardware="rpi-8gb")
                c2 = Compute.objects.create(node=n, hardware=rpi8)
                Compute.objects.filter(node=n, hardware=rpi8).update(zone="shield")

                ComputeSensor.objects.create(scope=c2, hardware=SensorHardware.objects.get(hardware="bme680"))
                ComputeSensor.objects.create(scope=c2, hardware=SensorHardware.objects.get(hardware="microphone"))
                ComputeSensor.objects.create(scope=c2, hardware=SensorHardware.objects.get(hardware="rainguage"))


