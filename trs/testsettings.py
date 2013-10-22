import os


SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATIC_URL = '/static/'
ROOT_URLCONF = 'trs.urls'
SECRET_KEY = 'sleutel van het secreet'
DEBUG = True
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BUILDOUT_DIR, 'var/db/test.db')},
    }
INSTALLED_APPS = [
    'trs',
    'south',
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    ]

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATICFILES_DIRS = [
    os.path.join(BUILDOUT_DIR, 'bower_components'),
    # ^^^ bower-managed files.
]
STATIC_URL = '/static/'
