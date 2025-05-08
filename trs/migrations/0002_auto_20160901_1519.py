from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trs", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="wbsoproject",
            name="number",
            field=models.IntegerField(
                verbose_name="Nummer", help_text="Gebruikt voor sortering"
            ),
        )
    ]
