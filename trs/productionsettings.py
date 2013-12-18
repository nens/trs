# He he, no secret production settings here in this open source repository of
# course :-)
# We import from a "trs-site" project that's in a private github repo.
# From here, we import the secret key and so.
from trs.testsettings import *

DEBUG = False
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'trs_cache',
        'TIMEOUT': 60 * 60 * 24 * 40,  # 40 days
        'OPTIONS': {'MAX_ENTRIES': 50000,
                },
        'KEY_PREFIX': 'trs',
    }
}

from trs_site.productionsettings import *
