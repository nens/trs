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
def money_with_decimal(value):
    """Return monetary value, rounded and nicely formatted. Fixed width font.
    """
    try:
        is_negative = (value < 0)
        value = abs(value)
        whole = value // 1
        remainder = value % 1
        if is_negative:
            whole = whole * -1
    except:  # Yes, a bare except: filters should not raise exceptions
        return value

    return mark_safe('<tt>%s,%02d</tt>' % (intcomma(round(whole)),
                                           round(100 * remainder)))


@register.filter
def moneydiff(value):
    """Return monetary value like money, but including a + sign when needed.
    """
    try:
        rounded = round(value)
    except:  # Yes, a bare except: filters should not raise exceptions
        return value
    if rounded > 0:
        return mark_safe('<tt>+%s</tt>' % intcomma(rounded))
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


@register.filter
def hoursdiff(value):
    """Return diff in hours, nice rounded and including a sign.
    """
    try:
        rounded = round(value)
    except:  # Yes, a bare except: filters should not raise exceptions
        return value
    if rounded > 0:
        return '+%s' % rounded
    return str(rounded)


@register.filter
def tabindex(value, index):
    """
    Add a tabindex attribute to the widget for a bound field.

    See http://stackoverflow.com/a/9250304/27401
    """
    value.field.widget.attrs['tabindex'] = index
    return value
