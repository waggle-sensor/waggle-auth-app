# Generated by Django 4.2.7 on 2024-01-31 01:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0013_node_commissioning_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="node",
            name="commissioning_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
