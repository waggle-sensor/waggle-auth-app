# Generated by Django 4.2.5 on 2023-11-03 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0034_rename_enclosure_rpi_nodebuild_extra_rpi"),
    ]

    operations = [
        migrations.CreateModel(
            name="LorawanConnection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "connection_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                (
                    "margin",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "expected_uplink_interval_sec",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "connection_type",
                    models.CharField(
                        choices=[("OTAA", "OTAA"), ("ABP", "ABP")], max_length=30
                    ),
                ),
            ],
            options={
                "verbose_name": "Lorawan Connection",
                "verbose_name_plural": "Lorawan Connections",
            },
        ),
        migrations.CreateModel(
            name="LorawanDevice",
            fields=[
                (
                    "deveui",
                    models.CharField(
                        max_length=16, primary_key=True, serialize=False, unique=True
                    ),
                ),
                (
                    "device_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "battery_level",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
            ],
            options={
                "verbose_name": "Lorawan Device",
                "verbose_name_plural": "Lorawan Devices",
            },
        ),
        migrations.CreateModel(
            name="LorawanKeys",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("app_key", models.CharField(blank=True, max_length=32, null=True)),
                ("network_Key", models.CharField(max_length=32)),
                ("app_session_key", models.CharField(max_length=32)),
                ("dev_address", models.CharField(max_length=8)),
                (
                    "lorawan_connection",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lorawankey",
                        to="manifests.lorawanconnection",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lorawan Key",
                "verbose_name_plural": "Lorawan Keys",
            },
        ),
        migrations.AddField(
            model_name="lorawanconnection",
            name="lorawan_device",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lorawanconnections",
                to="manifests.lorawandevice",
            ),
        ),
        migrations.AddField(
            model_name="lorawanconnection",
            name="node",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lorawanconnections",
                to="manifests.nodedata",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="lorawanconnection",
            unique_together={("node", "lorawan_device")},
        ),
    ]
