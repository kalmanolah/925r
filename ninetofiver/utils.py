"""Utils."""
from importlib import import_module
from calendar import monthrange
import os


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
