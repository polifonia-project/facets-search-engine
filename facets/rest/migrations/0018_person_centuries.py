# Generated by Django 4.0.2 on 2023-06-01 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0017_rename_dbpedia_url_person_wikidata_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='centuries',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]