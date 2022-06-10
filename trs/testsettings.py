from django.contrib.messages import constants as messages

import os


SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, ".."))

ROOT_URLCONF = "trs.urls"
SECRET_KEY = "sleutel van het secreet"
DEBUG = True
ALLOWED_HOSTS = ["trs.lizard.net", "localhost", "trs.nelen-schuurmans.nl"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
            ]
        },
    },
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BUILDOUT_DIR, "var/db/trs.db"),
    }
}
INSTALLED_APPS = [
    "trs",
    "lizard_auth_client",
    "raven.contrib.django.raven_compat",
    "gunicorn",
    "django.contrib.staticfiles",
    "django_extensions",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
]

MIDDLEWARE_CLASSES = [
    # Default stuff below.
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Defaults above, extra two below.
    # 'trs.middleware.TracebackLoggingMiddleware',
    "tls.TLSRequestMiddleware",
]

STATIC_ROOT = os.path.join(BUILDOUT_DIR, "staticfiles")  # Note: not var/static/!
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BUILDOUT_DIR, "bower_components"),
]
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.CachedStaticFilesStorage"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "memcache:11211",
        "TIMEOUT": 60 * 60 * 24 * 29,
        # ^^^ 29 days, memcached has a practical limit at 30 days
        "OPTIONS": {"MAX_ENTRIES": 500000},
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
        "null": {"level": "DEBUG", "class": "django.utils.log.NullHandler"},
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "logfile": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": os.path.join(BUILDOUT_DIR, "var", "log", "django.log"),
        },
        # sqllogfile is only used for demo purposes for showing off django's ORM.
        # "sqllogfile": {
        #     "level": "DEBUG",
        #     "class": "logging.FileHandler",
        #     "formatter": "verbose",
        #     "filename": os.path.join(BUILDOUT_DIR, "var", "log", "sql.log"),
        # },
        "sentry": {
            "level": "WARN",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "logfile", "sentry"],
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
            "handlers": ["console", "logfile", "sentry"],
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

# SSO
SSO_ENABLED = True
SSO_USE_V2_LOGIN = True
SSO_KEY = "trs_random_generated_key_to_identify_the_client"
SSO_SECRET = "trs_random_generated_secret_key_to_sign_exchanged_messages"
SSO_SERVER_API_START_URL = "https://sso.lizard.net/api2/"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "lizard_auth_client.backends.SSOBackend",
]

try:
    from .local_testsettings import *  # noqa
except ImportError:
    pass
