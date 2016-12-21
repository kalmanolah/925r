# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-21 14:30
from __future__ import unicode_literals

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ninetofiver', '0004_holiday'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employmentcontract',
            name='legal_country',
        ),
        migrations.AddField(
            model_name='company',
            name='country',
            field=django_countries.fields.CountryField(default='BE', max_length=2),
            preserve_default=False,
        ),
    ]
