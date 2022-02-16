# Generated by Django 4.0.2 on 2022-02-15 11:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Index',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='MusicDoc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_id', models.CharField(max_length=255, unique=True)),
                ('doc_type', models.CharField(max_length=255)),
                ('index', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rest.index')),
            ],
        ),
    ]
