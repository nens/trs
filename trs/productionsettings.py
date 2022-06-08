# He he, no secret production settings here in this open source repository of
# course :-)
# We import from a "trs-site" project that's in a private github repo.
# From here, we import the secret key and so.
from copy import copy
from trs.testsettings import *  # noqa


DEBUG = False


from trs_site.productionsettings import *
