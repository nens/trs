import os


SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATIC_URL = '/static/'
ROOT_URLCONF = 'trs.urls'
SECRET_KEY = 'sleutel van het secreet'
DEBUG = True
TEMPLATE_DEBUG = True
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BUILDOUT_DIR, 'var/db/test.db')},
    }
INSTALLED_APPS = [
    'trs',
    'south',
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
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Defaults above, extra one below.
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
            'format': '%(asctime)s %(name)s %(levelname)s\n%(message)s',
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
            'formatter': 'simple'
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
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['null'],  # Quiet by default!
            'propagate': False,
            'level': 'DEBUG',
        },
    }
}
# Start and end year are used for creating YearWeek objects for those years
# with the ``bin/django update_weeks`` command.
TRS_START_YEAR = 2012
TRS_END_YEAR = 2020
# ^^^ TODO: appconf defaults.

USE_L10N = True
USE_I18N = True
LANGUAGE_CODE = 'nl-nl'

LOGIN_URL = 'trs.login'
LOGOUT_URL = 'trs.logout'
