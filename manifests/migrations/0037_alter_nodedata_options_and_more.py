# Generated by Django 4.2.7 on 2023-12-13 17:28

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0036_nodedata_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="nodedata",
            name="commissioned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nodedata",
            name="gps_alt",
            field=models.FloatField(blank=True, null=True, verbose_name="Altitude"),
        ),
        migrations.AddField(
            model_name="nodedata",
            name="location",
            field=models.TextField(blank=True, verbose_name="Location"),
        ),
        migrations.AlterModelOptions(
            name="nodedata",
            options={"verbose_name": "node", "verbose_name_plural": "nodes"},
        ),
        migrations.RenameField(
            model_name="lorawandevice",
            old_name="device_name",
            new_name="name",
        ),
        migrations.AddField(
            model_name="lorawandevice",
            name="hardware",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="manifests.sensorhardware",
            ),
        ),
        migrations.AddField(
            model_name="lorawandevice",
            name="labels",
            field=models.ManyToManyField(blank=True, to="manifests.label"),
        ),
        migrations.AddField(
            model_name="lorawandevice",
            name="serial_no",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="lorawandevice",
            name="uri",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
        migrations.AddField(
            model_name="nodedata",
            name="date_joined",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="date joined"
            ),
        ),
        migrations.AddField(
            model_name="nodedata",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Designates whether this node should be treated as active. Unselect this instead of deleting nodes.",
                verbose_name="active",
            ),
        ),
        migrations.AlterField(
            model_name="computesensor",
            name="hardware",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="manifests.sensorhardware",
            ),
        ),
        migrations.AlterField(
            model_name="nodedata",
            name="vsn",
            field=models.CharField(max_length=10, unique=True, verbose_name="VSN"),
        ),
        migrations.AlterField(
            model_name="nodesensor",
            name="hardware",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="manifests.sensorhardware",
            ),
        ),
    ]
