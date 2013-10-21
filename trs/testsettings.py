ROOT_URLCONF = 'trs.urls'
SECRET_KEY = 'sleutel van het secreet'
DEBUG = True
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.db'},
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
