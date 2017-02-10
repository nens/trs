# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('trs', '0003_auto_20160901_1535'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payable',
            options={'verbose_name': 'factuur kosten derden', 'verbose_name_plural': 'facturen kosten derden', 'ordering': ('date', 'number')},
        ),
        migrations.AddField(
            model_name='project',
            name='profit',
            field=models.DecimalField(verbose_name='afdracht', decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='project',
            name='contract_amount',
            field=models.DecimalField(verbose_name='opdrachtsom', decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='project',
            name='reservation',
            field=models.DecimalField(verbose_name='reservering voor personele kosten', decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
