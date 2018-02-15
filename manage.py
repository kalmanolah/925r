#!/usr/bin/env python
import os
import sys
from ninetofiver.utils import get_django_configuration


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ninetofiver.settings')
    os.environ.setdefault('DJANGO_CONFIGURATION', get_django_configuration())

    try:
        from django.core.management import execute_from_command_line
        from configurations.management import execute_from_command_line  # noqa
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                'Couldn\'t import Django. Are you sure it\'s installed and '
                'available on your PYTHONPATH environment variable? Did you '
                'forget to activate a virtual environment?'
            )
        raise
    execute_from_command_line(sys.argv)
