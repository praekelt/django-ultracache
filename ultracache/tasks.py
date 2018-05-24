import json
try:
    from urllib.parse import urlparse
    from urllib.parse import quote
except ImportError:
    from urlparse import urlparse
    from urllib import quote

from celery import shared_task
try:
    import pika
    DO_TASK = True
except ImportError:
    DO_TASK = False

from django.conf import settings


@shared_task(max_retries=3, ignore_result=True)
def broadcast_purge(path, headers=None):
    if not DO_TASK:
        raise RuntimeError("Library pika>=0.11,<1.0 not found")

    try:
        url = settings.ULTRACACHE["rabbitmq-url"]
    except (AttributeError, KeyError):
        # Use same host as celery. Pika requires the path to be url
        # encoded. A typical broker URL setting remains effectively
        # unchanged but as soon as sub-paths are encountered this encoding
        # becomes necessary.
        parsed = urlparse(settings.CELERY_BROKER_URL)
        url = "%s://%s/%s" % (
            parsed.scheme,
            parsed.netloc,
            quote(parsed.path[1:], safe="")
        )
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.exchange_declare(exchange="purgatory", exchange_type="fanout")
    channel.basic_publish(
        exchange="purgatory",
        routing_key="",
        body=json.dumps({"path": path, "headers": headers or {}})
    )
    connection.close()
    return True
