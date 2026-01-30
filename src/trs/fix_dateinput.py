from django.forms.widgets import DateInput


def format_value_without_localizing(self, value):
    # Copied from Django
    if value == "" or value is None:
        return None
    # if self.is_localized:
    #     return formats.localize_input(value)
    return str(value)


def fix_it():
    # Default to the browser's standard datepicker. Called from apps.py
    DateInput.input_type = "date"
    DateInput.format = "%Y-%m-%d"
    DateInput.format_value = format_value_without_localizing
