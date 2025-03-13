# Generated by Django 5.1.4 on 2025-02-20 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_rename_structure_compound_structure_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='compound',
            old_name='classification',
            new_name='category',
        ),
        migrations.RemoveField(
            model_name='compound',
            name='canonical_smiles',
        ),
        migrations.RemoveField(
            model_name='compound',
            name='cid',
        ),
        migrations.RemoveField(
            model_name='compound',
            name='conjugate_base',
        ),
        migrations.RemoveField(
            model_name='compound',
            name='toxicity',
        ),
        migrations.AddField(
            model_name='compound',
            name='description',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='ic50',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='lelp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='inchi',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='inchikey',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='iupac_name',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='molecular_weight',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='smiles',
            field=models.TextField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='synonyms',
            field=models.URLField(blank=True, null=True),
        ),
    ]
