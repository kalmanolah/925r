# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-24 13:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ninetofiver', '0008_auto_20161224_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='performance_types',
            field=models.ManyToManyField(to='ninetofiver.PerformanceType'),
        ),
    ]
