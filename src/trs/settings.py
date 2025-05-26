# Note: there are no separate development settings! DEBUG is handled through
# enviroment variables. Likewise the secret key.

import os

import environ
import sentry_sdk
from django.contrib.messages import constants as messages
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env()

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, "..", ".."))

ROOT_URLCONF = "trs.urls"

DEBUG = env.bool("DEBUG", default=True)
SECRET_KEY = env("SECRET_KEY", default="sleutel van het secreet")
SENTRY_DSN = env("SENTRY_DSN", default="")


ALLOWED_HOSTS = ["trs.lizard.net", "localhost", "trs.nelen-schuurmans.nl"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    },
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "var/db/trs.db"),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
INSTALLED_APPS = [
    "trs",
    "gunicorn",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_extensions",
    "nens_auth_client",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
]

MIDDLEWARE = [
    # Whitenoise should be first.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Default stuff below.
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Defaults above, extra two below.
    # 'trs.middleware.TracebackLoggingMiddleware',
    "tls.TLSRequestMiddleware",
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # Note: not var/static/!
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "bower_components"),
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "memcache:11211",
        "TIMEOUT": 60 * 60 * 24 * 29,
        # ^^^ 29 days, memcached has a practical limit at 30 days
        "KEY_PREFIX": "trs",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(name)s %(levelname)s\n    %(message)s"},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "logfile": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": os.path.join(BASE_DIR, "var", "log", "django.log"),
        },
        # sqllogfile is only used for demo purposes for showing off django's ORM.
        # "sqllogfile": {
        #     "level": "DEBUG",
        #     "class": "logging.FileHandler",
        #     "formatter": "verbose",
        #     "filename": os.path.join(BASE_DIR, "var", "log", "sql.log"),
        # },
    },
    "loggers": {
        "": {
            "handlers": ["console", "logfile"],
            "propagate": True,
            "level": "DEBUG",
        },
        "django.db.backends": {
            # 'handlers': ['sqllogfile'],  # For demo purposes.
            "handlers": ["null"],
            "propagate": False,
            "level": "DEBUG",
        },
        "factory": {
            "handlers": ["console"],
            "propagate": False,
            "level": "INFO",  # Suppress the huge output in tests
        },
        "django.request": {
            "handlers": ["console", "logfile"],
            "propagate": False,
            "level": "ERROR",  # WARN also shows 404 errors
        },
    },
}


MESSAGE_TAGS = {messages.ERROR: "danger"}

# Start and end year are used for creating YearWeek objects for those years
# with the ``bin/django update_weeks`` command.
TRS_START_YEAR = 2000
TRS_END_YEAR = 2028
# ^^^ TODO: appconf defaults.

USE_L10N = True
USE_I18N = True
LANGUAGE_CODE = "nl-nl"
TIME_ZONE = "Europe/Amsterdam"

INTERNAL_IPS = ["localhost", "127.0.0.1"]

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
    )


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "nens_auth_client.backends.RemoteUserBackend",
    "nens_auth_client.backends.AcceptNensBackend",
    "nens_auth_client.backends.SSOMigrationBackend",
]
NENS_AUTH_ISSUER = env("NENS_AUTH_ISSUER", default="")
NENS_AUTH_CLIENT_ID = env("NENS_AUTH_CLIENT_ID", default="")
NENS_AUTH_CLIENT_SECRET = env("NENS_AUTH_CLIENT_SECRET", default="")

# Apparently this is needed now that we run gunicorn directly?
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
