from django.apps import AppConfig


class TRSAppConfig(AppConfig):
    name = "trs"
    verbose_name = "TRS"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Enable the signals
        from trs.signal_handlers import create_person  # NOQA
