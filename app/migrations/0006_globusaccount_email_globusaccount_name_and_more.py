# Generated by Django 4.1.1 on 2022-10-13 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_remove_user_globus_preferred_username_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="globusaccount",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="globusaccount",
            name="name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="globusaccount",
            name="preferred_username",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Preferred Username"
            ),
        ),
    ]
