# Generated by Django 4.0.2 on 2022-04-27 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0006_musicdoc_m21score_alter_musicdoc_musicfile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='musicdoc',
            name='musicfile',
        ),
    ]
