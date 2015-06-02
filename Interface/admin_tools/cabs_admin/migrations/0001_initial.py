# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Blacklist',
            fields=[
                ('address', models.CharField(max_length=32, serialize=False, primary_key=True, blank=True)),
                ('banned', models.NullBooleanField()),
                ('attempts', models.NullBooleanField()),
                ('timecleared', models.TimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'blacklist',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Current',
            fields=[
                ('user', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=32, blank=True)),
                ('machine', models.CharField(max_length=32, unique=True, serialize=False, primary_key=True)),
                ('confirmed', models.BooleanField()),
                ('connecttime', models.DateTimeField()),
            ],
            options={
                'db_table': 'current',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Machines',
            fields=[
                ('name', models.CharField(max_length=32)),
                ('machine', models.CharField(max_length=32, unique=True, serialize=False, primary_key=True)),
                ('active', models.BooleanField()),
                ('last_heartbeat', models.DateTimeField()),
            ],
            options={
                'db_table': 'machines',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Pools',
            fields=[
                ('name', models.CharField(max_length=32, serialize=False, primary_key=True)),
                ('description', models.CharField(max_length=1024, blank=True)),
                ('secondary', models.CharField(max_length=1024, blank=True)),
                ('groups', models.CharField(max_length=1024, blank=True)),
            ],
            options={
                'db_table': 'pools',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Whitelist',
            fields=[
                ('address', models.CharField(max_length=32, serialize=False, primary_key=True, blank=True)),
            ],
            options={
                'db_table': 'whitelist',
                'managed': False,
            },
            bases=(models.Model,),
        ),
    ]
