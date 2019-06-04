# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-12 15:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ninetofiver', '0057_auto_20180312_1553'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contractusergroup',
            name='contract_users',
        ),
        migrations.AddField(
            model_name='contractuser',
            name='contract_user_group',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='ninetofiver.ContractUserGroup'),
        ),
    ]
