# Generated by Django 4.0.2 on 2022-05-11 16:46

from django.db import migrations, models
import rest.models
import rest.utils


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0010_alter_index_name_alter_musicdoc_m21score'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='musicdoc',
            name='musicfile',
        ),
        migrations.AddField(
            model_name='musicdoc',
            name='abcfile',
            field=models.FileField(blank=True, null=True, storage=rest.utils.OverwriteStorage(), upload_to=rest.models.MusicDoc.upload_path),
        ),
        migrations.AddField(
            model_name='musicdoc',
            name='krnfile',
            field=models.FileField(blank=True, null=True, storage=rest.utils.OverwriteStorage(), upload_to=rest.models.MusicDoc.upload_path),
        ),
        migrations.AddField(
            model_name='musicdoc',
            name='meifile',
            field=models.FileField(blank=True, null=True, storage=rest.utils.OverwriteStorage(), upload_to=rest.models.MusicDoc.upload_path),
        ),
        migrations.AddField(
            model_name='musicdoc',
            name='musicxmlfile',
            field=models.FileField(blank=True, null=True, storage=rest.utils.OverwriteStorage(), upload_to=rest.models.MusicDoc.upload_path),
        ),
        migrations.AddField(
            model_name='musicdoc',
            name='xmlfile',
            field=models.FileField(blank=True, null=True, storage=rest.utils.OverwriteStorage(), upload_to=rest.models.MusicDoc.upload_path),
        ),
    ]
