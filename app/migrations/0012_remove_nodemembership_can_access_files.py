# Generated by Django 4.2.7 on 2024-01-30 23:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0011_node_files_public"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nodemembership",
            name="can_access_files",
        ),
    ]
