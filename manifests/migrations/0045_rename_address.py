# manually added by Francisco Lozano on 2024-02-13 22:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0044_remove_nodedata_location"),
    ]

    operations = [
        migrations.RenameField(
            model_name='nodedata',
            old_name='address',
            new_name='location',
        ),
        migrations.AlterField(
            model_name="nodedata",
            name="location",
            field=models.TextField(
                blank=True, db_column="location", verbose_name="Location"
            ),
        )
    ]