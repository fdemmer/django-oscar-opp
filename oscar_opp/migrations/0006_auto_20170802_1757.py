# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-02 15:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oscar_opp', '0005_auto_20170126_1530'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='error_code',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='error_message',
        ),
        migrations.AddField(
            model_name='transaction',
            name='result_description',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]