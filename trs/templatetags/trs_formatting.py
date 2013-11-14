# Template filter library for TRS.
from django import template
from django.utils.safestring import mark_safe
from django.contrib.humanize.templatetags.humanize import intcomma


register = template.Library()


@register.filter
def money(value):
    """Return monetary value, rounded and nicely formatted. Fixed width font.
    """
    try:
        rounded = round(value)
    except:  # Yes, a bare except: filters should not raise exceptions
        return value
    return mark_safe('<tt>%s</tt>' % intcomma(rounded))


@register.filter
def hours(value):
    """Return hours (hours booked, for instance), nicely rounded.
    """
    try:
        rounded = round(value)
    except:  # Yes, a bare except: filters should not raise exceptions
        return value
    return intcomma(rounded)
