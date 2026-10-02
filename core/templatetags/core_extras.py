import re

from django import template

register = template.Library()


@register.filter
def digits_only(value):
    """Strip everything but digits, for building wa.me links from a phone number."""
    if not value:
        return ""
    return re.sub(r"\D", "", str(value))
