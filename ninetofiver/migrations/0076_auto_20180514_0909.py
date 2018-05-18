# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-14 09:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ninetofiver', '0075_auto_20180514_0821'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contractestimate',
            old_name='role',
            new_name='contract_role',
        ),
        migrations.AlterUniqueTogether(
            name='contractestimate',
            unique_together=set([('contract', 'contract_role')]),
        ),
    ]