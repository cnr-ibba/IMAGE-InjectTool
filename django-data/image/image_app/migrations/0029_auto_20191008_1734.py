# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-08 15:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image_app', '0028_auto_20191003_1042'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dictbreed',
            options={'verbose_name': 'breed'},
        ),
        migrations.RemoveField(
            model_name='dictbreed',
            name='mapped_breed',
        ),
        migrations.RemoveField(
            model_name='dictbreed',
            name='mapped_breed_term',
        ),
        migrations.AddField(
            model_name='dictbreed',
            name='label',
            field=models.CharField(max_length=255, null=True, verbose_name='mapped breed'),
        ),
        migrations.AddField(
            model_name='dictbreed',
            name='term',
            field=models.CharField(help_text='Example: LBO_0000347', max_length=255, null=True, verbose_name='mapped breed term'),
        ),
    ]
