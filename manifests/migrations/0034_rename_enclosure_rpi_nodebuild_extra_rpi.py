# Generated by Django 4.2.5 on 2023-09-30 22:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0033_alter_nodebuild_enclosure_rpi"),
    ]

    operations = [
        migrations.RenameField(
            model_name="nodebuild",
            old_name="enclosure_rpi",
            new_name="extra_rpi",
        ),
    ]
