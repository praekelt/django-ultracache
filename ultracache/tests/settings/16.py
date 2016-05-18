import os


DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

ROOT_URLCONF = 'ultracache.tests.urls'

INSTALLED_APPS = (
    'ultracache',
    # Include tests because it declares models
    'ultracache.tests',
    'django.contrib.contenttypes',
    'django.contrib.sites',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SITE_ID = 1

SECRET_KEY = 'SECRET_KEY'

TEMPLATE_DIRS = (os.path.realpath(os.path.dirname(__file__)) + '/ultracache/tests/templates/',)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

ULTRACACHE = {
    'purge': {'method': 'ultracache.tests.utils.dummy_purger'}
}
