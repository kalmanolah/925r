"""Utils."""
from importlib import import_module
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import datetime
import os
import copy
from django.core.mail import send_mail as base_send_mail
from django.template.loader import render_to_string
from django.db.models import Q


DEFAULT_DJANGO_ENVIRONMENT = 'dev'


def get_django_environment():
    """Get the django environment."""
    return os.getenv('ENVIRONMENT', DEFAULT_DJANGO_ENVIRONMENT)


def get_django_configuration():
    """Get the django configuration name based on the current environment."""
    env = get_django_environment()

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


def month_date_range(year, month):
    """Get the date range for the given month."""
    from_date = datetime.date.today().replace(year=year, month=month, day=1)
    until_date = from_date.replace() + relativedelta(months=1) - relativedelta(days=1)
    return [from_date, until_date]


def dates_in_range(from_date, until_date):
    """Get all dates for the given date range."""
    dates = []
    current_date = copy.deepcopy(from_date)
    while current_date.strftime('%Y%m%d') <= until_date.strftime('%Y%m%d'):
        dates.append(copy.deepcopy(current_date))
        current_date += relativedelta(days=1)
    return dates


def hours_to_days(hours):
    """Convert hours to days."""
    return round(hours / 8, 2)


def format_duration(hours):
    """Format duration as a string."""
    if hours is None:
        return hours
    return '%(amount).2fh (%(days).2fd)' % {'amount': hours, 'days': hours_to_days(hours)}


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
        '',
        DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
        html_message=message
    )


def get_users_with_permission(permission):
    """Get a list of all users with a given permission."""
    from django.contrib.auth import models as auth_models

    users = (auth_models.User.objects
             .filter(Q(is_staff=True),
                     Q(is_superuser=True) |
                     Q(groups__permissions__codename=permission) |
                     Q(user_permissions__codename=permission))
             .distinct())
    return users