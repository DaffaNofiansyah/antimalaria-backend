# Generated by Django 5.1.4 on 2025-02-20 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_remove_compound_user_compound_prediction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='compound',
            name='cid',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
