# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-18 14:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('image_app', '0010_auto_20190215_1346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='developmental_stage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='image_app.DictStage'),
        ),
    ]