"""WSGI."""
import os
from ninetofiver import utils
from ninetofiver.utils import get_django_configuration


utils.DEFAULT_DJANGO_ENVIRONMENT = 'production'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ninetofiver.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', get_django_configuration())

from configurations.wsgi import get_wsgi_application  # noqa
application = get_wsgi_application()
