# Generated by Django 4.0.2 on 2022-04-28 22:39

from django.db import migrations, models
import rest.models
import rest.utils


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0008_rename_index_name_index_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='musicdoc',
            name='musicfile',
            field=models.FileField(blank=True, null=True, storage=rest.utils.OverwriteStorage(), upload_to=rest.models.MusicDoc.upload_path),
        ),
    ]
