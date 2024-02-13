# Generated by Django 4.2.7 on 2024-02-07 19:50

import address.models
from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("address", "0003_auto_20200830_1851"),
        ("manifests", "0040_address_nodedata_address_new"),
    ]

    operations = [
        migrations.AddField(
            model_name="nodedata",
            name="address_2",
            field=address.models.AddressField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="node",
                to="address.address",
            ),
        ),
    ]
