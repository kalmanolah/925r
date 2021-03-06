# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-04-24 08:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ninetofiver', '0062_userinfo_phone_number'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='leavetype',
            options={'base_manager_name': 'base_objects', 'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='performancetype',
            options={'base_manager_name': 'base_objects', 'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='leavetype',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
        ),
        migrations.AddField(
            model_name='performancetype',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
        ),
    ]
