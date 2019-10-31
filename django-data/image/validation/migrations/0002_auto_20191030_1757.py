# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-30 16:57
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('validation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='validationresult',
            name='messages',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=True, max_length=255), blank=True, default=list, size=None),
        ),
        migrations.AlterUniqueTogether(
            name='validationresult',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
