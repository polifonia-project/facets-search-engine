# Generated by Django 4.0.2 on 2022-04-20 13:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0004_alter_musicdoc_doc'),
    ]

    operations = [
        migrations.RenameField(
            model_name='musicdoc',
            old_name='doc',
            new_name='musicfile',
        ),
    ]
