from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trs", "0004_auto_20170125_1029"),
    ]

    operations = [
        migrations.CreateModel(
            name="ThirdPartyEstimate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "added",
                    models.DateTimeField(
                        verbose_name="toegevoegd op", auto_now_add=True
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="omschrijving"
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        max_digits=12,
                        default=0,
                        verbose_name="bedrag exclusief",
                        decimal_places=2,
                    ),
                ),
                (
                    "added_by",
                    models.ForeignKey(
                        null=True,
                        blank=True,
                        verbose_name="toegevoegd door",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        verbose_name="project",
                        related_name="third_party_estimates",
                        to="trs.Project",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "begrote kosten derden",
                "verbose_name_plural": "begrote kosten derden",
            },
        ),
        migrations.AlterField(
            model_name="budgetitem",
            name="amount",
            field=models.DecimalField(
                max_digits=12,
                help_text="Dit zijn kosten, dus een positief getal wordt van het projectbudget afgetrokken. ",
                default=0,
                verbose_name="bedrag exclusief",
                decimal_places=2,
            ),
        ),
    ]
