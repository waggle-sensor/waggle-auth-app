# Generated by Django 4.2.7 on 2024-01-18 23:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0038_alter_computehardware_hw_model_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="computehardware",
            name="hw_model",
            field=models.CharField(
                help_text="The model number of your sensor preferably without the manufacturer name in it.",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="resourcehardware",
            name="hw_model",
            field=models.CharField(
                help_text="The model number of your sensor preferably without the manufacturer name in it.",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="sensorhardware",
            name="hw_model",
            field=models.CharField(
                help_text="The model number of your sensor preferably without the manufacturer name in it.",
                max_length=30,
            ),
        ),
    ]