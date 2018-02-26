"""Markdown."""
from django import template
from django.utils.safestring import mark_safe
import markdown as md


register = template.Library()


@register.filter
def markdown(value):
    res = md.markdown(value)
    print(res)
    res = mark_safe(res)

    return res
