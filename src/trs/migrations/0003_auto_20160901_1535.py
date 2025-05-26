import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("trs", "0002_auto_20160901_1519")]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="user",
            field=models.OneToOneField(
                null=True,
                blank=True,
                verbose_name="gebruiker",
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                help_text="De interne (django) gebruiker die deze persoon is. Dit wordt normaliter automatisch gekoppeld op basis vande loginnaam zodra de gebruiker voor de eerste keer inlogt.",
            ),
        )
    ]
