import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trs", "0005_auto_20170206_2128")]

    operations = [
        migrations.AlterField(
            model_name="thirdpartyestimate",
            name="amount",
            field=models.DecimalField(
                verbose_name="bedrag exclusief",
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
                default=0,
                decimal_places=2,
            ),
        )
    ]
