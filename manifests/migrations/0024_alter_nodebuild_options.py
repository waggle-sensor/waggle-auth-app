# Generated by Django 4.2.5 on 2023-09-22 18:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0023_alter_nodebuild_vsn"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="nodebuild",
            options={"verbose_name_plural": "Node Builds"},
        ),
    ]