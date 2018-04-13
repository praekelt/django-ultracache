import requests

from django.conf import settings


def broadcast(path, headers=None):
    # The preferred methody requires RabbitMQ and celery being installed and
    # configured.
    from ultracache.tasks import broadcast_purge
    broadcast_purge.delay(path, headers)


def varnish(path, headers=None):
    # See https://www.varnish-software.com/static/book/Cache_invalidation.html
    loc = settings.ULTRACACHE["purge"]["method"]["url"].rstrip("/") + "/" \
        + path.lstrip("/")
    try:
        r = requests.request("PURGE", loc, timeout=1, headers=headers or {})
    except requests.exceptions.RequestException:
        pass


def nginx(path, headers=None):
    # See https://github.com/FRiCKLE/ngx_cache_purge

    # Simplest case - one node
    loc = settings.ULTRACACHE["purge"]["method"]["url"].rstrip("/") + "/" \
        + path.lstrip("/")
    try:
        r = requests.request("PURGE", loc, timeout=1, headers=headers or {})
    except requests.exceptions.RequestException:
        pass
