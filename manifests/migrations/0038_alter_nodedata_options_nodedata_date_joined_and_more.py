# Generated by Django 4.2.5 on 2023-12-08 04:59

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0037_alter_lorawandevice_device_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="nodedata",
            options={"verbose_name": "node", "verbose_name_plural": "nodes"},
        ),
        migrations.AddField(
            model_name="nodedata",
            name="date_joined",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="date joined"
            ),
        ),
        migrations.AddField(
            model_name="nodedata",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Designates whether this node should be treated as active. Unselect this instead of deleting nodes.",
                verbose_name="active",
            ),
        ),
        migrations.AlterField(
            model_name="nodedata",
            name="vsn",
            field=models.CharField(max_length=10, unique=True, verbose_name="VSN"),
        ),
    ]
