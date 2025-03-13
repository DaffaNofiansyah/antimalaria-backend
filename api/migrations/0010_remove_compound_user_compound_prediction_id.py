# Generated by Django 5.1.4 on 2025-02-20 06:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_mlmodel_prediction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compound',
            name='user',
        ),
        migrations.AddField(
            model_name='compound',
            name='prediction_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.prediction'),
        ),
    ]
