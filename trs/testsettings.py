import os


SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATIC_URL = '/static/'
ROOT_URLCONF = 'trs.urls'
SECRET_KEY = 'sleutel van het secreet'
DEBUG = True
ALLOWED_HOSTS = ['trs.lizard.net', 'localhost']
TEMPLATE_DEBUG = True
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BUILDOUT_DIR, 'var/db/trs.db')},
}
INSTALLED_APPS = [
    'trs',
    'lizard_auth_client',
    'south',
    'gunicorn',
    'debug_toolbar',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_nose',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
]
MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # Default stuff below.
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Defaults above, extra two below.
    # 'trs.middleware.TracebackLoggingMiddleware',
    'tls.TLSRequestMiddleware',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATICFILES_DIRS = [
    os.path.join(BUILDOUT_DIR, 'bower_components'),
    # ^^^ bower-managed files.
]
STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)s %(levelname)s\n    %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BUILDOUT_DIR,
                                     'var', 'log', 'django.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'logfile',],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['null'],  # Quiet by default!
            'propagate': False,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['console', 'logfile'],
            'propagate': False,
            'level': 'ERROR',  # WARN also shows 404 errors
        },
    }
}
# Start and end year are used for creating YearWeek objects for those years
# with the ``bin/django update_weeks`` command.
TRS_START_YEAR = 2000
TRS_END_YEAR = 2020
# ^^^ TODO: appconf defaults.

USE_L10N = True
USE_I18N = True
LANGUAGE_CODE = 'nl-nl'
TIME_ZONE = 'Europe/Amsterdam'

INTERNAL_IPS = ['localhost', '127.0.0.1']

# SSO
SSO_ENABLED = True
# A key identifying this client. Can be published.
SSO_KEY = 'trs_random_generated_key_to_identify_the_client'
# A *secret* shared between client and server.
# Used to sign the messages exchanged between them.
SSO_SECRET = 'trs_random_generated_secret_key_to_sign_exchanged_messages'
# URL used to redirect the user to the SSO server
# Note: needs a trailing slash
SSO_SERVER_PUBLIC_URL = 'http://sso.lizard.net/'
# URL used for server-to-server communication
# Note: needs a trailing slash
SSO_SERVER_PRIVATE_URL = 'http://somewhere:someport/'
# Don't copy is_staff/is_superuser
SSO_SYNCED_USER_KEYS = ['first_name', 'last_name', 'email', 'is_active']


try:
    from .local_testsettings import *
except ImportError:
    pass
