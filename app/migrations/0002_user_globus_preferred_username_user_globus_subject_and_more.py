# Generated by Django 4.1.1 on 2022-10-12 20:13

import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="globus_preferred_username",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Globus Preferred Username",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="globus_subject",
            field=models.UUIDField(
                blank=True, null=True, verbose_name="Globus Subject"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="ssh_public_keys",
            field=models.TextField(
                blank=True,
                validators=[app.models.validate_ssh_public_key_list],
                verbose_name="SSH public keys",
            ),
        ),
    ]
