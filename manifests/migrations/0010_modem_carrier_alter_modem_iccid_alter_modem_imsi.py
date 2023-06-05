# Generated by Django 4.2.1 on 2023-06-05 16:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "manifests",
            "0009_alter_modem_iccid_alter_modem_imei_alter_modem_imsi_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="modem",
            name="carrier",
            field=models.CharField(
                blank=True, default="", max_length=64, verbose_name="Carrier"
            ),
        ),
        migrations.AlterField(
            model_name="modem",
            name="iccid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=64,
                validators=[django.core.validators.RegexValidator("^[0-9]{20}$")],
                verbose_name="ICCID",
            ),
        ),
        migrations.AlterField(
            model_name="modem",
            name="imsi",
            field=models.CharField(
                blank=True,
                default="",
                max_length=64,
                validators=[django.core.validators.RegexValidator("^[0-9]{15}$")],
                verbose_name="IMSI",
            ),
        ),
    ]
