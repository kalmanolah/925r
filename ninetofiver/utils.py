"""Utils."""
from importlib import import_module
import os


def get_django_configuration():
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
