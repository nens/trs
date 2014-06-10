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

# Keep middleware classes in sync between dev and prod. Only diff is the lack
# of debugtoolbarmiddleware in development.
MIDDLEWARE_CLASSES = (
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

from trs_site.productionsettings import *
