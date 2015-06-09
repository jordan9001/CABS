# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cabs_admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('setting', models.CharField(max_length=32, unique=True, serialize=False, primary_key=True)),
                ('value', models.CharField(max_length=64)),
            ],
            options={
                'db_table': 'settings',
                'managed': False,
            },
            bases=(models.Model,),
        ),
    ]
