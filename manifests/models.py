from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class NodePhase(models.TextChoices):
    DEPLOYED = "Deployed"
    MAINTENANCE = "Maintenance"
    STANDBY = "Standby"
    AWAITING_DEPLOYMENT = "Awaiting Deployment"
    SHIPMENT_PENDING = "Shipment Pending"


class NodeType(models.TextChoices):
    BLADE = "Blade", "Blade"
    WSN = "WSN", "WSN"


class NodeData(models.Model):
    vsn = models.CharField("VSN", max_length=30, unique="True")
    name = models.CharField("Node ID", max_length=30, blank=True)
    phase = models.CharField(
        "Phase", max_length=30, null=True, choices=NodePhase.choices, blank=True
    )
    tags = models.ManyToManyField("Tag", blank=True)
    notes = models.TextField(blank=True)
    computes = models.ManyToManyField(
        "ComputeHardware", through="Compute", related_name="computes"
    )
    resources = models.ManyToManyField(
        "ResourceHardware", through="Resource", related_name="resources"
    )
    gps_lat = models.FloatField("Latitude", blank=True, null=True)
    gps_lon = models.FloatField("Longitude", blank=True, null=True)
    address = models.TextField("Address", blank=True)
    registered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.vsn

    class Meta:
        verbose_name_plural = "Nodes"


ModemModels = [
    ("mtcm2", "Multi-Tech MTCM2-L4G1-B03-KIT"),
    ("other", "Other"),
]

ModemSIMs = [
    ("anl-nu", "Northwestern"),
    ("anl-dawn", "ANL-DAWN"),
    ("anl-vto", "ANL-VTO"),
    ("other", "Other"),
]


class Modem(models.Model):
    node = models.OneToOneField(
        NodeData, blank=True, null=True, on_delete=models.SET_NULL
    )
    imei = models.CharField(
        "IMEI",
        max_length=64,
        unique=True,
        validators=[
            RegexValidator("^[0-9]{15}$"),
        ],
    )
    imsi = models.CharField(
        "IMSI",
        max_length=64,
        blank=True,
        default="",
        validators=[RegexValidator("^[0-9]{15}$")],
    )
    iccid = models.CharField(
        "ICCID",
        max_length=64,
        blank=True,
        default="",
        validators=[RegexValidator("^[0-9]{20}$")],
    )
    carrier = models.CharField(
        "Carrier Code",
        blank=True,
        default="",
        max_length=64,
        validators=[RegexValidator("^[0-9]{,20}$")],
    )
    model = models.CharField(
        "Model", max_length=64, choices=ModemModels, default="mtcm2"
    )
    sim_type = models.CharField(
        "SIM Type", max_length=64, choices=ModemSIMs, default="other"
    )

    def __str__(self):
        return self.imei


class AbstractHardware(models.Model):
    hardware = models.CharField(max_length=100)
    hw_model = models.CharField(max_length=30, blank=True)
    hw_version = models.CharField(max_length=30, blank=True)
    sw_version = models.CharField(max_length=30, blank=True)
    manufacturer = models.CharField(max_length=255, default="", blank=True)
    datasheet = models.CharField(max_length=255, default="", blank=True)
    capabilities = models.ManyToManyField("Capability", blank=True)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True


class ComputeHardware(AbstractHardware):
    cpu = models.CharField(max_length=30, blank=True)
    cpu_ram = models.CharField(max_length=30, blank=True)
    gpu_ram = models.CharField(max_length=30, blank=True)
    shared_ram = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.hardware

    class Meta:
        verbose_name_plural = "Compute Hardware"


class ResourceHardware(AbstractHardware):
    def __str__(self):
        return self.hardware

    class Meta:
        verbose_name_plural = "Resource Hardware"


class SensorHardware(AbstractHardware):
    def __str__(self):
        return self.hardware

    class Meta:
        verbose_name_plural = "Sensor Hardware"


class Capability(models.Model):
    capability = models.CharField(max_length=30)

    def __str__(self):
        return self.capability

    class Meta:
        verbose_name_plural = "Capabilities"


class Compute(models.Model):
    ZONE_CHOICES = (
        ("core", "core"),
        ("agent", "agent"),
        ("shield", "shield"),
        ("detector", "detector (deprecated! use enclosure instead!)"),
        ("enclosure", "enclosure"),
    )

    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, blank=True)
    hardware = models.ForeignKey(ComputeHardware, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=30, default="", blank=True)
    serial_no = models.CharField(max_length=30, default="", blank=True)
    zone = models.CharField(max_length=30, choices=ZONE_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Compute"


class AbstractSensor(models.Model):
    hardware = models.ForeignKey(SensorHardware, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=30, blank=True)
    labels = models.ManyToManyField("Label", blank=True)
    serial_no = models.CharField(max_length=30, default="", blank=True)
    uri = models.CharField(max_length=256, default="", blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class NodeSensor(AbstractSensor):
    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, blank=True)
    scope = models.CharField(max_length=30, default="global", blank=True)


class ComputeSensor(AbstractSensor):
    scope = models.ForeignKey(Compute, on_delete=models.CASCADE, blank=True)


class Resource(models.Model):
    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, blank=True)
    hardware = models.ForeignKey(ResourceHardware, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=30, blank=True)


class Tag(models.Model):
    tag = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.tag

    def natural_key(self):
        return self.tag


class Label(models.Model):
    label = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.label

    def natural_key(self):
        return self.label


class NodeBuildProject(models.Model):
    class Meta:
        verbose_name_plural = "Node Build Projects"

    name = models.CharField("Name", max_length=64)

    def __str__(self):
        return self.name


class NodeBuild(models.Model):
    class Meta:
        verbose_name_plural = "Node Builds"

    vsn = models.CharField(
        "VSN",
        max_length=10,
        unique=True,
    )
    type = models.CharField(
        "Type",
        max_length=10,
        choices=NodeType.choices,
        default=NodeType.WSN,
    )
    project = models.ForeignKey(
        NodeBuildProject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    agent = models.BooleanField(
        "Agent",
        default=False,
    )
    shield = models.BooleanField(
        "Shield",
        default=False,
    )
    extra_rpi = models.BooleanField(
        "Extra RPi",
        default=False,
    )
    modem = models.BooleanField(
        "Modem",
        default=False,
    )
    modem_sim_type = models.CharField(
        "Modem SIM Type",
        max_length=64,
        blank=True,
        null=True,
        choices=ModemSIMs,
        default=None,
    )
    top_camera = models.ForeignKey(
        SensorHardware,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    bottom_camera = models.ForeignKey(
        SensorHardware,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    left_camera = models.ForeignKey(
        SensorHardware,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    right_camera = models.ForeignKey(
        SensorHardware,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def clean(self):
        super().clean()

        if self.modem is False and self.modem_sim_type is not None:
            raise ValidationError(
                {
                    "modem": "Modem must be set to True if SIM Type is specified.",
                    "sim_type": "SIM Type should be empty if Modem is False.",
                }
            )
            
class LoRaWANDevice(models.Model):
    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, related_name='lorawandevices', null=False,blank=False)
    deveui = models.CharField(max_length=16, primary_key=True, unique=True, null=False, blank=False)
    device_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    battery_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    margin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    expected_uplink_interval_sec = models.IntegerField(blank=True, null=True)
    # add more fields later like device class, using OTAA or ADB, app name, app key, datasheet etc- Flozano

    class Meta:
        verbose_name = "LoRaWAN Device"
        verbose_name_plural = "LoRaWAN Devices"

    def __str__(self):
        return str(self.device_name) + '-' + str(self.deveui)

    def natural_key(self):
        return self.deveui
