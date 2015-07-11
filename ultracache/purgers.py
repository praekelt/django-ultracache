import requests

from django.conf import settings


def varnish(path):
    # See https://www.varnish-software.com/static/book/Cache_invalidation.html
    loc = settings.ULTRACACHE['purge']['method']['url'].rstrip('/') + '/' \
        + path.lstrip('/')
    try:
        r = requests.request('PURGE', loc, timeout=1)
    except requests.exceptions.RequestException:
        pass


def nginx(path):
    # See https://github.com/FRiCKLE/ngx_cache_purge
    loc = settings.ULTRACACHE['purge']['method']['url'].rstrip('/') + '/' \
        + path.lstrip('/')
    try:
        r = requests.request('GET', loc, timeout=1)
    except requests.exceptions.RequestException:
        pass
