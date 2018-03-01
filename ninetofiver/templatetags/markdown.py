"""Markdown."""
from django import template
from django.utils.safestring import mark_safe
import markdown as md


register = template.Library()


@register.filter
def markdown(value):
    """Convert the given markdown value to HTML."""
    res = md.markdown(value)
    res = mark_safe(res)

    return res
