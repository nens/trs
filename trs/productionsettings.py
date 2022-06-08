# He he, no secret production settings here in this open source repository of
# course :-)
# We import from a "trs-site" project that's in a private github repo.
# From here, we import the secret key and so.
from copy import copy
from trs.testsettings import *


DEBUG = False

for unwanted_in_production in [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "debug_toolbar",
]:
    MIDDLEWARE_CLASSES = copy(MIDDLEWARE_CLASSES)
    INSTALLED_APPS = copy(INSTALLED_APPS)
    for where in [MIDDLEWARE_CLASSES, INSTALLED_APPS]:
        if unwanted_in_production in where:
            where.remove(unwanted_in_production)

from trs_site.productionsettings import *
