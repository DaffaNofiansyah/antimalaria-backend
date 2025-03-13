# Generated by Django 5.1.4 on 2025-01-17 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compound',
            name='smilescode',
        ),
        migrations.AddField(
            model_name='compound',
            name='cid',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='molecular_formula',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='molecular_weight',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='smiles',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
