# Generated by Django 4.2.7 on 2024-08-07 20:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "manifests",
            "0040_nodebuildprojectfocus_nodebuildprojectpartner_site_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="compute",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Indicates whether this item is currently expected to be active. Unselect this to temporarily mark the item as inactive without deleting it, maintaining its configuration.",
                verbose_name="active",
            ),
        ),
        migrations.AddField(
            model_name="computesensor",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Indicates whether this item is currently expected to be active. Unselect this to temporarily mark the item as inactive without deleting it, maintaining its configuration.",
                verbose_name="active",
            ),
        ),
        migrations.AddField(
            model_name="lorawandevice",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Indicates whether this item is currently expected to be active. Unselect this to temporarily mark the item as inactive without deleting it, maintaining its configuration.",
                verbose_name="active",
            ),
        ),
        migrations.AddField(
            model_name="nodesensor",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Indicates whether this item is currently expected to be active. Unselect this to temporarily mark the item as inactive without deleting it, maintaining its configuration.",
                verbose_name="active",
            ),
        ),
    ]
    