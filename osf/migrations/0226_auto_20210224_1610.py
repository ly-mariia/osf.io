# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2021-02-24 16:10
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osf', '0225_auto_20201119_2027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nodelicense',
            name='license_id',
            field=models.CharField(help_text='A unique id for the license. for example', max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='nodelicense',
            name='name',
            field=models.CharField(help_text='The name of the license', max_length=256, unique=True),
        ),
        migrations.AlterField(
            model_name='nodelicense',
            name='properties',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=128), blank=True, default=list, help_text="The custom elements in a license's text surrounded with curly brackets for example: <i>{year,copyrightHolders}</i>", size=None),
        ),
        migrations.AlterField(
            model_name='nodelicense',
            name='text',
            field=models.TextField(help_text='The text of the license with custom properties surround by curly brackets, for example: <i>Copyright (c) {{year}}, {{copyrightHolders}} All rights reserved.</i>'),
        ),
        migrations.AlterField(
            model_name='nodelicense',
            name='url',
            field=models.URLField(blank=True, help_text="The license's url for example: <i>http://opensource.org/licenses/BSD-3-Clause</i>"),
        ),
    ]
