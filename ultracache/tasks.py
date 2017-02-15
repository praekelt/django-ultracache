try:
    import pika
    from celery.task import shared_task
    DO_TASK = True
except ImportError:
    DO_TASK = False

from django.conf import settings

if DO_TASK:
    @shared_task(max_retries=3, ignore_result=True)
    def broadcast_purge(path):

        # Use same host as celery
        host, _ = settings.CELERY_BROKER_URL.split("/")[2].split(":")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange="purgatory", type="fanout")
        channel.basic_publish(
            exchange="purgatory",
            routing_key="",
            body=path
        )
        connection.close()
        return True
