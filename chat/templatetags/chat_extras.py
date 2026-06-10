"""Custom template filters for the chat app."""

import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def to_json(value):
    """Serialize a value to JSON for use in templates."""
    return mark_safe(json.dumps(value))
