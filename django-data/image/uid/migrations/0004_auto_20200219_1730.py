# Generated by Django 2.2.10 on 2020-02-19 16:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uid', '0003_auto_20200129_1630'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dictrole',
            options={'ordering': ['label'], 'verbose_name': 'role'},
        ),
        migrations.AlterField(
            model_name='organization',
            name='role',
            field=models.ForeignKey(help_text="The organization role, for example 'submitter'", on_delete=django.db.models.deletion.PROTECT, to='uid.DictRole'),
        ),
        migrations.AlterField(
            model_name='person',
            name='role',
            field=models.ForeignKey(help_text="Your role, for example 'submitter'", null=True, on_delete=django.db.models.deletion.PROTECT, to='uid.DictRole'),
        ),
    ]
