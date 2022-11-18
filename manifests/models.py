from django.db import models


# Create your models here.

# NodeData
class NodeData(models.Model):

    VSN = models.CharField(max_length=30, unique="True")
    name = models.CharField(max_length=30)
    tags = models.ManyToManyField("Tag")
    computes = models.ManyToManyField("Hardware", through="Compute", related_name="computes")
    resources = models.ManyToManyField("Hardware", through="Resource", related_name="resources")
    gps_lat = models.FloatField(blank=True)
    gps_lan = models.FloatField(blank=True)


    def __str__(self):
         return self.VSN

# Hardware
class Hardware(models.Model):

    hardware = models.CharField(max_length=30)
    hw_model = models.CharField(max_length=30, blank=True)
    hw_version = models.CharField(max_length=30, blank=True)
    sw_version = models.CharField(max_length=30, blank=True)
    datasheet = models.CharField(max_length=30, default="<url>", blank=True)
    cpu = models.CharField(max_length=30, blank=True)
    cpu_ram = models.CharField(max_length=30, blank=True)
    gpu_ram = models.CharField(max_length=30, blank=True)
    shared_ram = models.BooleanField(default=False, blank=True)
    capabilities = models.ManyToManyField("Capability", blank=True)

    def __str__(self):
         return self.hardware

# Capability
class Capability(models.Model):

    capability = models.CharField(max_length=30)

    def __str__(self):
         return self.capability

# Compute
class Compute(models.Model):

    ZONE_CHOICES = (
        ("core", "core"),
        ("agent", "agent"),
        ("detector", "detector")
    )

    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, blank=True)
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=30, default="", blank=True)
    serial_no = models.CharField(max_length=30, default="<MAC ADDRESS>", blank=True)
    zone = models.CharField(max_length=30, choices=ZONE_CHOICES, blank=True)

    def __str__(self):
        return self.name

# Sensor
class CommonSensor(models.Model):
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=30, blank=True)
    labels = models.ManyToManyField("Label", blank=True)

    class Meta:
        abstract = True

class NodeSensor(CommonSensor):
    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, blank=True)
    scope = models.CharField(max_length=30, default="global", blank=True)

class ComputeSensor(CommonSensor):
    scope = models.ForeignKey(Compute, on_delete=models.CASCADE, blank=True)

# Resource
class Resource(models.Model):
    node = models.ForeignKey(NodeData, on_delete=models.CASCADE, blank=True)
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, blank=True)
    name = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.name

# Tag
class Tag(models.Model):
    tag = models.CharField(max_length=30, unique="True")

    def __str__(self):
        return self.tag

    def natural_key(self):
        return self.tag

# Label
class Label(models.Model):
    label = models.CharField(max_length=30)

    def __str__(self):
        return self.label