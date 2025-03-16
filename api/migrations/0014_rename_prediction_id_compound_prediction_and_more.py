# Generated by Django 5.1.4 on 2025-03-15 23:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_alter_compound_description_alter_compound_inchi_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='compound',
            old_name='prediction_id',
            new_name='prediction',
        ),
        migrations.RemoveField(
            model_name='prediction',
            name='model_id',
        ),
        migrations.AddField(
            model_name='prediction',
            name='model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.mlmodel'),
        ),
        migrations.AlterField(
            model_name='prediction',
            name='jenis_malaria',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='prediction',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
