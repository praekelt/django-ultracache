import urllib
import urlparse

try:
    import pika
    from celery import shared_task
    DO_TASK = True
except ImportError:
    DO_TASK = False

from django.conf import settings


@shared_task(max_retries=3, ignore_result=True)
def broadcast_purge(path):
    if not DO_TASK:
        raise RuntimeError("Libraries celery and/ or pika not found")

    try:
        url = settings.ULTRACACHE["rabbitmq-url"]
    except (AttributeError, KeyError):
        # Use same host as celery. Pika requires the path to be url
        # encoded. A typical broker URL setting remains effectively
        # unchanged but as soon as sub-paths are encountered this encoding
        # becomes necessary.
        parsed = urlparse.urlparse(settings.CELERY_BROKER_URL)
        url = "%s://%s/%s" % (
            parsed.scheme,
            parsed.netloc,
            urllib.quote(parsed.path[1:], safe="")
        )
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.exchange_declare(exchange="purgatory", type="fanout")
    channel.basic_publish(
        exchange="purgatory",
        routing_key="",
        body=path
    )
    connection.close()
    return True
