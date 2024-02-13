# manually added by Francisco Lozano on 2024-02-13 22:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0045_rename_address"),
    ]

    operations = [
        migrations.RenameField(
            model_name='nodedata',
            old_name='address_new',
            new_name='address',
        )
    ]