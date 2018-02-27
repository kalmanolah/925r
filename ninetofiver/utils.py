"""Utils."""
from importlib import import_module
from calendar import monthrange
import os
from django.core.mail import send_mail as base_send_mail
from django.template.loader import render_to_string


def get_django_configuration():
    """Get the django configuration name based on the current environment."""
    env = os.getenv('ENVIRONMENT', 'dev')

    env_map = {
        'staging': 'Stag',
        'demo': 'Demo',
        'production': 'Prod',
    }

    return env_map.get(env, 'Dev')


def str_import(string):
    """Import a class from a string."""
    module, attr = string.rsplit('.', maxsplit=1)
    module = import_module(module)
    attr = getattr(module, attr)

    return attr


def merge_dicts(*dicts):
    """Merge two dicts."""
    result = {}
    [result.update(x) for x in dicts]

    return result


def days_in_month(year, month):
    """Get the amount of days in a month."""
    return monthrange(year, month)[1]


def send_mail(recipients, subject, template, context={}):
    """Send a mail from a template to the given recipients."""
    from ninetofiver.settings import DEFAULT_FROM_EMAIL
    from django_settings_export import _get_exported_settings

    if type(recipients) not in [list, tuple]:
        recipients = [recipients]

    context['settings'] = _get_exported_settings()
    message = render_to_string(template, context=context)

    base_send_mail(
        subject,
        message,
        DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )
