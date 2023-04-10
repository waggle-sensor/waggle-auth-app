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


def gps_coord_or_none(row, k):
    s = row[k].strip()
    if not s:
        return None
    return float(s)


def add_wsn(row, node):
    # add below hardwares to every node:
    # 1. xaviernx
    compute = Compute.objects.create(
        node=node,
        hardware=ComputeHardware.objects.get(hardware="xaviernx"),
        name="nxcore",
        zone="core",
        serial_no=row["node_id"][4:],
    )

    # 2. bme280 on nxcore
    ComputeSensor.objects.create(
        scope=compute,
        hardware=SensorHardware.objects.get(hardware="bme280"),
        name="bme280",
    )

    # 3. gps on nxcore
    ComputeSensor.objects.create(
        scope=compute,
        hardware=SensorHardware.objects.get(hardware="gps"),
        name="gps",
    )

    # usbhub-10port
    Resource.objects.create(
        node=node,
        hardware=ResourceHardware.objects.get(hardware="usbhub-10port"),
        name="usbhub",
    )

    # switch
    Resource.objects.create(
        node=node,
        hardware=ResourceHardware.objects.get(hardware="switch"),
        name="switch",
    )

    # 5. wagman
    Resource.objects.create(
        node=node,
        hardware=ResourceHardware.objects.get(hardware="wagman"),
        name="wagman",
    )

    # 6. psu: psu-B0BD for nodes before (but not include) W040, psu-BBBD for nodes after W040
    # 7. wifi: for nodes after W040
    if row["flag"] == "group1":
        Resource.objects.create(
            node=node,
            hardware=ResourceHardware.objects.get(hardware="psu-b0bd"),
            name="psu",
        )
    else:
        Resource.objects.create(
            node=node,
            hardware=ResourceHardware.objects.get(hardware="psu-bbbd"),
            name="psu",
        )
        Resource.objects.create(
            node=node,
            hardware=ResourceHardware.objects.get(hardware="wifi"),
            name="wifi",
        )
        Resource.objects.create(
            node=node,
            hardware=ResourceHardware.objects.get(hardware="usbhub-2port"),
            name="usbhub-2",
        )

    if row["modem"] == "yes":
        Resource.objects.create(
            node=node,
            hardware=ResourceHardware.objects.get(hardware="modem"),
            name="modem",
        )

    modem_sim_hardware_mapping = {
        "NU-Sage": "modem-sim-nu",
        "ANL-VTO": "modem-sim-anl-vto",
        "ANL-DAWN": "modem-sim-anl-dawn",
        "end-user": "modem-sim-other",
    }

    matches = {k for k in modem_sim_hardware_mapping.keys() if k in row["modem_sim"]}

    if len(matches) == 0:
        pass
    elif len(matches) == 1:
        hardware = modem_sim_hardware_mapping[list(matches)[0]]
        Resource.objects.create(
            node=node,
            hardware=ResourceHardware.objects.get(hardware=hardware),
            name="modem-sim",
        )
    else:
        raise RuntimeError(f"ambiguous modem for {row}")

    # infer cameras
    for camera in ["top_camera", "bottom_camera", "left_camera", "right_camera"]:
        if row[camera] == "none":
            continue
        hardware = infer_camera_hardware_from_name(row[camera].strip())
        NodeSensor.objects.create(
            node=node,
            hardware=SensorHardware.objects.get(hardware=hardware),
            name=camera,
        )

    # nx_agent
    if row["nx_agent"] == "yes":
        Compute.objects.create(
            node=node,
            hardware=ComputeHardware.objects.get(hardware="xaviernx-poe"),
            zone="agent",
            name="nxagent",
        )

    # shield
    if row["shield"] == "yes":
        rpi_hardware = "rpi-4gb" if row["flag"] == "group1" else "rpi-8gb"
        rpi = ComputeHardware.objects.get(hardware=rpi_hardware)
        compute = Compute.objects.create(
            node=node, hardware=rpi, zone="shield", name="rpi"
        )
        ComputeSensor.objects.create(
            scope=compute,
            hardware=SensorHardware.objects.get(hardware="bme680"),
            name="bme680",
        )
        ComputeSensor.objects.create(
            scope=compute,
            hardware=SensorHardware.objects.get(hardware="microphone"),
            name="microphone",
        )
        ComputeSensor.objects.create(
            scope=compute,
            hardware=SensorHardware.objects.get(hardware="rainguage"),
            name="raingauge",
        )


def add_blade(row, node):
    compute = Compute.objects.create(
        node=node,
        hardware=ComputeHardware.objects.get(hardware="dell-xr2"),
        name="sbcore",
        zone="core",
        serial_no=row["node_id"][4:],
    )


with open("scripts/data/nodedata.csv") as file:
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

        for k in row.keys():
            row[k] = row[k].strip()

        for k in ["vsn", "node_id"]:
            row[k] = row[k].upper()

        node = NodeData.objects.create(
            vsn=row["vsn"],
            name=row["node_id"],
            gps_lat=gps_coord_or_none(row, "gps_lat"),
            gps_lon=gps_coord_or_none(row, "gps_lon"),
        )

        if row["vsn"].startswith("W"):
            add_wsn(row, node)
        elif row["vsn"].startswith("V"):
            add_blade(row, node)
