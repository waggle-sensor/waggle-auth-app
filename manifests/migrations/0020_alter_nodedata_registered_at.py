# Generated by Django 4.2.5 on 2023-09-19 21:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0019_nodedata_registered_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nodedata",
            name="registered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
