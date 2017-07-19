"""
Django settings for ninetofiver project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
import ldap
import os
import yaml

from configurations import Configuration
from django_auth_ldap.config import LDAPSearch
from django_auth_ldap.config import LDAPSearchUnion

CFG_FILE_PATH = os.path.expanduser(os.environ.get('CFG_FILE_PATH', '/etc/925r/config.yml'))


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Base(Configuration):

    """Base configuration."""

    @classmethod
    def pre_setup(cls):
        super(Base, cls).pre_setup()
        cls._load_cfg_file()
        cls._process_cfg()

    @classmethod
    def _load_cfg_file(cls):
        data = None

        try:
            with open(CFG_FILE_PATH, 'r') as f:
                data = yaml.load(f)
        except:
            pass

        if data:
            for key, value in data.items():
                setattr(cls, key, value)

    @classmethod
    def _process_cfg(cls):
        cls.AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
            *[LDAPSearch(x[0], getattr(ldap, x[1]), x[2]) for x in cls.AUTH_LDAP_USER_SEARCHES]
        )

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = '$6_rj^w8_*ihrkohpckeq4028ai1*no1cw1vp*2%oe8+#gp1sj'

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    ALLOWED_HOSTS = []

    # Apps included here will be included
    # in the test suite
    NINETOFIVER_APPS = [
        'ninetofiver',
    ]

    # Application definition
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'rest_framework_swagger',
        # 'django_filters',
        'rest_framework_filters',
        'corsheaders',
        'polymorphic',
        'oauth2_provider',
        'crispy_forms',
        'django_gravatar',
        'django_countries',
        'rangefilter',
        'django_admin_listfilter_dropdown',
#        'django_extensions'        
    ] + NINETOFIVER_APPS

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    ROOT_URLCONF = 'ninetofiver.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            # 'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django_settings_export.settings_export',
                ],
                'loaders': [
                    ('pypugjs.ext.django.Loader', (
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    )),
                ],
                'builtins': ['pypugjs.ext.django.templatetags'],
            },
        },
    ]

    WSGI_APPLICATION = 'ninetofiver.wsgi.application'

    # Database
    # https://docs.djangoproject.com/en/1.10/ref/settings/#databases

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'YAYATA',
            'USER': 'root',
            'PASSWORD': 'rootroot',
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }

    # Password validation
    # https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/1.10/topics/i18n/

    LANGUAGE_CODE = 'en-us'

    TIME_ZONE = 'UTC'

    USE_I18N = True

    USE_L10N = True

    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.10/howto/static-files/
    STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
    STATIC_URL = '/static/'

    # User-uploaded files
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

    # Caching
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

    # Auth
    LOGIN_URL = 'login'
    LOGOUT_URL = 'logout'

    # REST framework
    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'oauth2_provider.ext.rest_framework.OAuth2Authentication',
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.BasicAuthentication',
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
        'DEFAULT_FILTER_BACKENDS': (
            'django_filters.rest_framework.DjangoFilterBackend',
        ),
        'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        'DEFAULT_PAGINATION_CLASS': 'ninetofiver.pagination.CustomizablePageNumberPagination',
        'PAGE_SIZE': 25,
    }

    # Swagger
    SWAGGER_SETTINGS = {
        'SECURITY_DEFINITIONS': {
            # 'basic': {
            #     'type': 'basic'
            # },
            # 'primary': {
            #     'type': 'oauth2',
            #     'flow': 'implicit',
            #     'tokenUrl': '/oauth/v2/token',
            #     'authorizationUrl': '/oauth/v2/authorize',
            #     'scopes': {
            #         'write': 'Write data',
            #         'read': 'Read data',
            #     }
            # },
        },
        'DOC_EXPANSION': 'list',
        'SHOW_REQUEST_HEADERS': True,
        'JSON_EDITOR': False,
        # 'APIS_SORTER': 'alpha',
        # 'OPERATIONS_SORTER': 'method',
        'VALIDATOR_URL': None,
    }

    # Crispy forms
    CRISPY_TEMPLATE_PACK = 'bootstrap3'

    # Gravatar
    GRAVATAR_DEFAULT_IMAGE = 'identicon'

    # Registration
    ACCOUNT_ACTIVATION_DAYS = 7
    REGISTRATION_OPEN = True

    # CORS
    CORS_ORIGIN_ALLOW_ALL = True

    # Exported settings available in templates
    SETTINGS_EXPORT = [
        'DEBUG',
        'REGISTRATION_OPEN',
    ]

    # Authentication using LDAP
    AUTHENTICATION_BACKENDS = [
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

    AUTH_LDAP_SERVER_URI = "ldap://ldap"
    AUTH_LDAP_START_TLS = False
    AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=org"
    AUTH_LDAP_BIND_PASSWORD = "admin"
    AUTH_LDAP_USER_SEARCHES = [
        ['dc=example,dc=org', 'SCOPE_SUBTREE', '(cn=%(user)s)'],
    ]
    AUTH_LDAP_USER_ATTR_MAP = {
        'email': 'mail',
        'first_name': 'givenName',
        'last_name': 'sn',
    }
    AUTH_LDAP_ALWAYS_UPDATE_USER = True

    # REDMINE 
    REDMINE_URL = None 
    REDMINE_API_KEY = None


class Dev(Base):

    """Dev configuration."""

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


class Prod(Base):

    """Prod configuration."""

    DEBUG = False
    ALLOWED_HOSTS = ['localhost']

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db-prod.sqlite3'),
        }
    }

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.expanduser('~/.ninetofiver_cache'),
            'TIMEOUT': 60 * 60 * 24 * 7 * 365,
            'OPTIONS': {
                'MAX_ENTRIES': 10000
            }
        }
    }

    REGISTRATION_OPEN = False


class TravisCI(Base):

    """Travis-CI configuration."""

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'travis_ci_db',
            'USER': 'travis',
            'PASSWORD': '',
            'HOST': '127.0.0.1',
        }
    }

    REDMINE_URL = os.getenv('REDMINE_URL')
    REDMINE_API_KEY = os.getenv('REDMINE_API_KEY')