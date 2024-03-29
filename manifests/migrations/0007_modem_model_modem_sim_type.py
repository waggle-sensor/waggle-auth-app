# Generated by Django 4.2.1 on 2023-06-04 17:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0006_alter_modem_imei_alter_modem_node"),
    ]

    operations = [
        migrations.AddField(
            model_name="modem",
            name="model",
            field=models.CharField(
                choices=[
                    ("mtcm2", "Multi-Tech MTCM2-L4G1-B03-KIT"),
                    ("other", "Other"),
                ],
                default="mtcm2",
                max_length=32,
                verbose_name="Model",
            ),
        ),
        migrations.AddField(
            model_name="modem",
            name="sim_type",
            field=models.CharField(
                choices=[
                    ("anl-dawn", "ANL-DAWN"),
                    ("anl-vto", "ANL-VTO"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=32,
                verbose_name="SIM Type",
            ),
        ),
    ]
