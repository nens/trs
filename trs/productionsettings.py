# He he, no secret production settings here in this open source repository of
# course :-)
# We import from a "trs-site" project that's in a private github repo.
# From here, we import the secret key and so.
from trs.testsettings import *

DEBUG = False
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BUILDOUT_DIR, 'var/cache'),
        'TIMEOUT': 60 * 60 * 24 * 4,  # 4 days
        'OPTIONS': {'MAX_ENTRIES': 50000,
                },
    }
}

from trs_site.productionsettings import *
