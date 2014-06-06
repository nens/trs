# He he, no secret production settings here in this open source repository of
# course :-)
# We import from a "trs-site" project that's in a private github repo.
# From here, we import the secret key and so.
from trs.testsettings import *

DEBUG = False
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'localhost:11211',
        'TIMEOUT': 60 * 60 * 24 * 29,
        # ^^^ 29 days, memcached has a practical limit at 30 days
        'OPTIONS': {'MAX_ENTRIES': 50000},
        'KEY_PREFIX': 'trs',
    }
}

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'
RAVEN_CONFIG = {
    'dsn': 'https://bac9c8a84f00417a8460e7c5be2db105:437c6d1c2b744efca09619149038dbf3@sentry.lizard.net/8',
}

from trs_site.productionsettings import *
