# Generated by Django 4.1.8 on 2023-04-07 18:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0003_computesensor_serial_no_computesensor_uri_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="computehardware",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="resourcehardware",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="sensorhardware",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
