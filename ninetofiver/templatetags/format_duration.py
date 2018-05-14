"""Format duration."""
from django import template
from ninetofiver.utils import format_duration as format_duration_base


register = template.Library()


@register.filter
def format_duration(value):
    """Convert the given decimal value to a duration string."""
    return format_duration_base(value)
