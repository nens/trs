import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trs", "0007_auto_20170209_0327")]

    operations = [
        migrations.AddField(
            model_name="project",
            name="software_development",
            field=models.DecimalField(
                validators=[django.core.validators.MinValueValidator(0)],
                decimal_places=2,
                max_digits=12,
                default=0,
                verbose_name="kosten software development (€1000/dag)",
            ),
        )
    ]
