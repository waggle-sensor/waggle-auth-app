# Generated by Django 4.2.5 on 2023-09-30 22:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0032_nodebuild_enclosure_rpi"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nodebuild",
            name="enclosure_rpi",
            field=models.BooleanField(default=False, verbose_name="Extra RPi"),
        ),
    ]
