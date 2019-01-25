# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-25 11:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('image_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecieSynonim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=255)),
                ('dictspecie', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='image_app.DictSpecie')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='image_app.DictCountry')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='speciesynonim',
            unique_together=set([('dictspecie', 'language', 'word')]),
        ),
    ]
