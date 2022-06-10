# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("trs", "0006_auto_20170206_2226")]

    operations = [
        migrations.AlterModelOptions(
            name="thirdpartyestimate",
            options={
                "verbose_name_plural": "kosten derden",
                "verbose_name": "kosten derden",
            },
        ),
        migrations.AlterField(
            model_name="project",
            name="is_accepted",
            field=models.BooleanField(
                help_text="Project is goedgekeurd door de PM  en kan qua begroting niet meer gewijzigd worden.",
                default=False,
                verbose_name="goedgekeurd",
            ),
        ),
    ]
