import os


DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

ROOT_URLCONF = "ultracache.tests.urls"

INSTALLED_APPS = (
    "ultracache",
    # Include tests because it declares models
    "ultracache.tests",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "rest_framework",
    "template_multiprocessing",
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'uc',
    }
}

SITE_ID = 1

SECRET_KEY = "SECRET_KEY"

TEMPLATE_DIRS = (os.path.realpath(os.path.dirname(__file__)) + "/ultracache/tests/templates/",)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
)

ULTRACACHE = {
    "purge": {"method": "ultracache.tests.utils.dummy_purger"},
    "drf": {"viewsets": {"*": {}}}
}
