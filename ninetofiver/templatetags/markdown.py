"""Markdown."""
from django import template
from django.utils.safestring import mark_safe
import markdown2 as md


register = template.Library()


@register.filter
def markdown(value):
    """Convert the given markdown value to HTML."""
    res = value
    res = md.markdown(res, extras=['tag-friendly'])
    res = mark_safe(res)

    return res
