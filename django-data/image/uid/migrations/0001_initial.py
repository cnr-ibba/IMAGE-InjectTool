# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-29 16:24
from __future__ import unicode_literals

import common.fields
import common.storage
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uid.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Animal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('status', models.SmallIntegerField(choices=[(1, 'Loaded'), (2, 'Submitted'), (4, 'Need Revision'), (5, 'Ready'), (6, 'Completed')], default=1, help_text='example: Submitted')),
                ('last_changed', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_submitted', models.DateTimeField(blank=True, null=True)),
                ('alternative_id', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('material', models.CharField(default='Organism', editable=False, max_length=255)),
                ('birth_date', models.DateField(blank=True, help_text='example: 2019-04-01', null=True)),
                ('birth_location', models.CharField(blank=True, max_length=255, null=True)),
                ('birth_location_latitude', models.FloatField(blank=True, null=True)),
                ('birth_location_longitude', models.FloatField(blank=True, null=True)),
                ('birth_location_accuracy', models.SmallIntegerField(choices=[(0, 'missing geographic information'), (1, 'country level'), (2, 'region level'), (3, 'precise coordinates'), (4, 'unknown accuracy level')], default=0, help_text='example: unknown accuracy level, country level')),
            ],
            bases=(uid.mixins.BioSampleMixin, uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictBreed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
                ('supplied_breed', models.CharField(max_length=255)),
                ('label', models.CharField(max_length=255, null=True, verbose_name='mapped breed')),
                ('term', models.CharField(help_text='Example: LBO_0000347', max_length=255, null=True, verbose_name='mapped breed term')),
            ],
            options={
                'verbose_name': 'breed',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictCountry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
            ],
            options={
                'verbose_name': 'country',
                'verbose_name_plural': 'countries',
                'ordering': ['label'],
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictDevelStage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
            ],
            options={
                'verbose_name': 'developmental stage',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
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
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'role',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictSex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'sex',
                'verbose_name_plural': 'sex',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictSpecie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
                ('general_breed_label', models.CharField(blank=True, help_text='Example: cattle breed', max_length=255, null=True, verbose_name='general breed label')),
                ('general_breed_term', models.CharField(blank=True, help_text='Example: LBO_0000001', max_length=255, null=True, verbose_name='general breed term')),
            ],
            options={
                'verbose_name': 'specie',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='DictUberon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: submitter', max_length=255)),
                ('term', models.CharField(help_text='Example: EFO_0001741', max_length=255, null=True)),
                ('confidence', models.SmallIntegerField(choices=[(0, 'High'), (1, 'Good'), (2, 'Medium'), (3, 'Low'), (4, 'Manually Curated')], help_text='example: Manually Curated', null=True)),
            ],
            options={
                'verbose_name': 'organism part',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Ontology',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('library_name', models.CharField(help_text='Each value must be unique', max_length=255, unique=True)),
                ('library_uri', models.URLField(blank=True, help_text='Each value must be unique and with a valid URL', max_length=500, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name_plural': 'ontologies',
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(blank=True, help_text='One line, comma separated', max_length=255, null=True)),
                ('URI', models.URLField(blank=True, help_text='Web site', max_length=500, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='uid.DictCountry')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='uid.DictRole')),
            ],
            options={
                'ordering': ['name', 'country'],
            },
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initials', models.CharField(blank=True, max_length=255, null=True)),
                ('affiliation', models.ForeignKey(help_text='The institution you belong to', null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.Organization')),
                ('role', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.DictRole')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='person_set', to=settings.AUTH_USER_MODEL)),
            ],
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doi', models.CharField(help_text='Valid Digital Object Identifier', max_length=255)),
            ],
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('status', models.SmallIntegerField(choices=[(1, 'Loaded'), (2, 'Submitted'), (4, 'Need Revision'), (5, 'Ready'), (6, 'Completed')], default=1, help_text='example: Submitted')),
                ('last_changed', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_submitted', models.DateTimeField(blank=True, null=True)),
                ('alternative_id', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('material', models.CharField(default='Specimen from Organism', editable=False, max_length=255)),
                ('protocol', models.CharField(blank=True, max_length=255, null=True)),
                ('collection_date', models.DateField(blank=True, help_text='example: 2019-04-01', null=True)),
                ('collection_place_latitude', models.FloatField(blank=True, null=True)),
                ('collection_place_longitude', models.FloatField(blank=True, null=True)),
                ('collection_place', models.CharField(blank=True, max_length=255, null=True)),
                ('collection_place_accuracy', models.SmallIntegerField(choices=[(0, 'missing geographic information'), (1, 'country level'), (2, 'region level'), (3, 'precise coordinates'), (4, 'unknown accuracy level')], default=0, help_text='example: unknown accuracy level, country level')),
                ('animal_age_at_collection', models.IntegerField(blank=True, null=True)),
                ('animal_age_at_collection_units', models.SmallIntegerField(blank=True, choices=[(0, 'minutes'), (1, 'hours'), (2, 'days'), (3, 'weeks'), (4, 'months'), (5, 'years')], help_text='example: years', null=True)),
                ('availability', models.CharField(blank=True, help_text='Either a link to a web page giving information on who to contact or an e-mail address to contact about availability. If neither available, please use the value no longer available', max_length=255, null=True)),
                ('storage', models.SmallIntegerField(blank=True, choices=[(0, 'ambient temperature'), (1, 'cut slide'), (2, 'frozen, -80 degrees Celsius freezer'), (3, 'frozen, -20 degrees Celsius freezer'), (4, 'frozen, liquid nitrogen'), (5, 'frozen, vapor phase'), (6, 'paraffin block'), (7, 'RNAlater, frozen -20 degrees Celsius'), (8, 'TRIzol, frozen'), (9, 'paraffin block at ambient temperatures (+15 to +30 degrees Celsius)'), (10, 'freeze dried'), (11, 'frozen, -40 degrees Celsius freezer')], help_text='How the sample was stored', null=True)),
                ('storage_processing', models.SmallIntegerField(blank=True, choices=[(0, 'cryopreservation in liquid nitrogen (dead tissue)'), (1, 'cryopreservation in dry ice (dead tissue)'), (2, 'cryopreservation of live cells in liquid nitrogen'), (3, 'cryopreservation, other'), (4, 'formalin fixed, unbuffered'), (5, 'formalin fixed, buffered'), (6, 'formalin fixed and paraffin embedded'), (7, 'freeze dried (vaiable for reproduction)'), (8, 'freeze dried')], help_text='How the sample was prepared for storage', null=True)),
                ('preparation_interval', models.IntegerField(blank=True, null=True)),
                ('preparation_interval_units', models.SmallIntegerField(blank=True, choices=[(0, 'minutes'), (1, 'hours'), (2, 'days'), (3, 'weeks'), (4, 'months'), (5, 'years')], help_text='example: years', null=True)),
                ('animal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uid.Animal')),
                ('developmental_stage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.DictDevelStage')),
                ('organism_part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.DictUberon')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('physiological_stage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.DictPhysioStage')),
                ('publication', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='uid.Publication')),
            ],
            bases=(uid.mixins.BioSampleMixin, uid.mixins.BaseMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Example: Roslin Sheep Atlas', max_length=255, verbose_name='Submission title')),
                ('project', models.CharField(default='IMAGE', editable=False, max_length=25)),
                ('description', models.CharField(help_text='Example: The Roslin Institute Sheep Gene Expression Atlas Project', max_length=255)),
                ('gene_bank_name', models.CharField(help_text='example: CryoWeb', max_length=255)),
                ('datasource_type', models.SmallIntegerField(choices=[(0, 'CryoWeb'), (1, 'Template'), (2, 'CRB-Anim')], help_text='example: CryoWeb', verbose_name='Data source type')),
                ('datasource_version', models.CharField(help_text='examples: "2018-04-27", "version 1.5"', max_length=255, verbose_name='Data source version')),
                ('uploaded_file', common.fields.ProtectedFileField(storage=common.storage.ProtectedFileSystemStorage(), upload_to='data_source/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.SmallIntegerField(choices=[(0, 'Waiting'), (1, 'Loaded'), (2, 'Submitted'), (3, 'Error'), (4, 'Need Revision'), (5, 'Ready'), (6, 'Completed')], default=0, help_text='example: Waiting')),
                ('message', models.TextField(blank=True, null=True)),
                ('gene_bank_country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='uid.DictCountry')),
                ('organization', models.ForeignKey(help_text='Who owns the data', on_delete=django.db.models.deletion.PROTECT, to='uid.Organization')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            bases=(uid.mixins.BaseMixin, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='dictuberon',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictspecie',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictsex',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictrole',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictphysiostage',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictdevelstage',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictcountry',
            unique_together=set([('label', 'term')]),
        ),
        migrations.AddField(
            model_name='dictbreed',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='uid.DictCountry'),
        ),
        migrations.AddField(
            model_name='dictbreed',
            name='specie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='uid.DictSpecie'),
        ),
        migrations.AddField(
            model_name='animal',
            name='breed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='uid.DictBreed'),
        ),
        migrations.AddField(
            model_name='animal',
            name='father',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='father_of', to='uid.Animal'),
        ),
        migrations.AddField(
            model_name='animal',
            name='mother',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mother_of', to='uid.Animal'),
        ),
        migrations.AddField(
            model_name='animal',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='animal',
            name='publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='uid.Publication'),
        ),
        migrations.AddField(
            model_name='animal',
            name='sex',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.DictSex'),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('gene_bank_name', 'gene_bank_country', 'datasource_type', 'datasource_version', 'owner')]),
        ),
        migrations.AlterUniqueTogether(
            name='sample',
            unique_together=set([('name', 'animal')]),
        ),
        migrations.AlterUniqueTogether(
            name='dictbreed',
            unique_together=set([('supplied_breed', 'specie', 'country')]),
        ),
        migrations.AlterUniqueTogether(
            name='animal',
            unique_together=set([('name', 'breed')]),
        ),
    ]