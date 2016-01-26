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

    # Simplest case - one node
    loc = settings.ULTRACACHE['purge']['method']['url'].rstrip('/') + '/' \
        + path.lstrip('/')
    try:
        r = requests.request('PURGE', loc, timeout=1)
    except requests.exceptions.RequestException:
        pass

    # More nodes
    for host in ('196.1.2.3', '196.1.2.4'):
        loc = 'http://%s%s' % (host, path)
        try:
            r = requests.request('PURGE', loc, timeout=1)
        except requests.exceptions.RequestException:
            pass

    # Using RabbitMQ to avoid needing knowledge of the nodes. See
    # twisted/monitor.py on how to handle the messages. You will need pika
    # installed.
    rabbit_host = '192.1.2.5'
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbit_host)
    )
    channel = connection.channel()
    channel.exchange_declare(exchange="purgatory", type="fanout")
    channel.basic_publish(
        exchange="purgatory",
        routing_key="",
        body=path
    )
    connection.close()

