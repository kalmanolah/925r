"""Redmine specific settings."""
import yaml
import os

from configurations import Configuration
from ninetofiver import settings

class Base(Configuration):

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'Error'),
            },
        },
    }
