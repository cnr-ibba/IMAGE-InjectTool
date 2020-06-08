# Generated by Django 2.2.9 on 2020-01-27 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biosample', '0002_auto_20200124_1712'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrphanSample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('biosample_id', models.CharField(max_length=255, unique=True)),
                ('found_at', models.DateTimeField(auto_now_add=True)),
                ('ignore', models.BooleanField(default=False, help_text='Should I ignore this record or not?')),
                ('name', models.CharField(max_length=255)),
                ('removed', models.BooleanField(default=False, help_text='Is this sample still available?')),
                ('removed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
