# Generated by Django 4.2.7 on 2024-01-31 00:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0012_remove_nodemembership_can_access_files"),
    ]

    operations = [
        migrations.AddField(
            model_name="node",
            name="commissioning_date",
            field=models.DateTimeField(null=True),
        ),
    ]