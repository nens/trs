# Generated by Django 3.2.16 on 2024-12-16 18:59

from django.db import migrations
from django.db import models

import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("trs", "0009_auto_20220708_1535"),
    ]

    operations = [
        migrations.CreateModel(
            name="MPC",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="naam")),
                (
                    "description",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="omschrijving"
                    ),
                ),
                (
                    "target",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="omzetdoelstelling",
                    ),
                ),
            ],
            options={
                "verbose_name": "Markt-product-combinatie",
                "verbose_name_plural": "Markt-product-combinaties",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="person",
            name="mpc",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="persons",
                to="trs.mpc",
                verbose_name="markt-product-combinatie",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="mpc",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="projects",
                to="trs.mpc",
                verbose_name="markt-product-combinatie",
            ),
        ),
    ]
