# Generated by Django 4.2.5 on 2023-12-11 21:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0036_nodedata_project"),
    ]

    operations = [
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
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="manifests.sensorhardware",
            ),
            preserve_default=False,
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
    ]
