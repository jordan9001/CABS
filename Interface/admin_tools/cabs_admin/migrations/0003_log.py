# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cabs_admin', '0002_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('msg_type', models.CharField(max_length=16, blank=True)),
                ('message', models.CharField(max_length=1024, blank=True)),
            ],
            options={
                'db_table': 'log',
                'managed': False,
            },
            bases=(models.Model,),
        ),
    ]
