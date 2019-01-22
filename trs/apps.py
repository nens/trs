from django.apps import AppConfig


class TRSAppConfig(AppConfig):
    name = "trs"
    verbose_name = "TRS"

    def ready(self):
        # Enable the signals
        from trs.signal_handlers import create_person  # NOQA
