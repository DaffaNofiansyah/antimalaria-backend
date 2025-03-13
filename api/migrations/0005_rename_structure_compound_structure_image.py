

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_compound_structure'),
    ]

    operations = [
        migrations.RenameField(
            model_name='compound',
            old_name='structure',
            new_name='structure_image',
        ),
    ]
