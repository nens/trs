# He he, no secret production settings here in this open source repository of
# course :-)
# We import from a "trs-site" project that's in a private github repo.
# From here, we import the secret key and so.
from trs.testsettings import *
from copy import copy

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

for unwanted_in_production in ['debug_toolbar.middleware.DebugToolbarMiddleware',
                               'debug_toolbar']:
    MIDDLEWARE_CLASSES = copy(MIDDLEWARE_CLASSES)
    INSTALLED_APPS = copy(INSTALLED_APPS)
    for where in [MIDDLEWARE_CLASSES, INSTALLED_APPS]:
        if unwanted_in_production in where:
            where.remove(unwanted_in_production)

INSTALLED_APPS = ['opbeat.contrib.django'] + INSTALLED_APPS
MIDDLEWARE_CLASSES = ['opbeat.contrib.django.middleware.OpbeatAPMMiddleware'] + MIDDLEWARE_CLASSES

from trs_site.productionsettings import *
