# Generated by Django 4.2.7 on 2024-02-19 18:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0047_nodebuildprojectfocus_nodedata_focus"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="nodebuildprojectfocus",
            options={"verbose_name_plural": "Node Build Project Focuses"},
        ),
        migrations.AlterModelOptions(
            name="nodebuildprojectpartner",
            options={"verbose_name_plural": "Node Build Project Partners"},
        ),
        migrations.AddField(
            model_name="nodebuild",
            name="focus",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="manifests.nodebuildprojectfocus",
            ),
        ),
        migrations.AddField(
            model_name="nodebuild",
            name="partner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="manifests.nodebuildprojectpartner",
            ),
        ),
    ]
