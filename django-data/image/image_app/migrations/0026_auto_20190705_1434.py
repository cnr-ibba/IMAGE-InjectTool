# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-05 12:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import image_app.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('image_app', '0025_auto_20190701_1351'),
    ]

    operations = [
        migrations.CreateModel(
            name='DictPhysioStage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
            ],
            options={
                'verbose_name': 'physiological stage',
            },
            bases=(image_app.mixins.BaseMixin, models.Model),
        ),
        migrations.RenameModel(
            old_name='DictStage',
            new_name='DictDevelStage',
        ),
        migrations.AddField(
            model_name='sample',
            name='preparation_interval_units',
            field=models.SmallIntegerField(blank=True, choices=[(0, 'minutes'), (1, 'hours'), (2, 'days'), (3, 'weeks'), (4, 'months'), (5, 'years')], help_text='example: years', null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='physiological_stage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='image_app.DictPhysioStage'),
        ),
        migrations.AlterUniqueTogether(
            name='dictphysiostage',
            unique_together=set([('label', 'term')]),
        ),
    ]