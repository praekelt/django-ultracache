import json
import traceback
from multiprocessing.pool import ThreadPool
from optparse import OptionParser
from time import sleep

import pika
import requests
import yaml


class Consumer:

    channel = None
    connection = None

    def __init__(self):
        self.pool = ThreadPool()
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                  help="Configuration file", metavar="FILE")
        (options, args) = parser.parse_args()
        config_file = options.config
        self.config = {}
        if config_file:
            self.config = yaml.load(open(config_file)) or {}

    def log(self, msg):
        name = self.config.get("logfile", None)
        if not name:
            return
        if name == "stdout":
            print(msg)
            return
        fp = open(name, "a")
        try:
            fp.write(msg + "\n")
        finally:
            fp.close()

    def connect(self):
        parameters = pika.URLParameters(
            self.config.get(
                "rabbit-url",
                "amqp://guest:guest@127.0.0.1:5672/%2F"
            )
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange="purgatory", exchange_type="fanout"
        )
        queue = self.channel.queue_declare(exclusive=True)
        queue_name = queue.method.queue
        self.channel.queue_bind(exchange="purgatory", queue=queue_name)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            self.on_message, queue=queue_name, no_ack=False, exclusive=True
        )

    def on_message(self, channel, method_frame, header_frame, body):
        self.pool.apply_async(self.handle_message, (body,))
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def handle_message(self, body):
        if body:
            try:
                di = json.loads(body)
            except ValueError:
                path = body
                headers = {}
            else:
                path = di["path"]
                headers = di["headers"]
            self.log("Purging %s with headers %s" % (path, str(headers)))
            host = self.config.get("host", None)
            try:
                if host:
                    final_headers = {"Host": host}
                    final_headers.update(headers)
                    response = requests.request(
                        "PURGE", "http://" \
                            + self.config.get("proxy-address", "127.0.0.1") + path,
                        headers=final_headers,
                        timeout=10
                    )
                else:
                    response = requests.request(
                        "PURGE", "http://" \
                            + self.config.get("proxy-address", "127.0.0.1") + path,
                        timeout=10,
                        headers=headers
                    )
            except Exception as exception:
                msg = traceback.format_exc()
                self.log("Error purging %s: %s" % (path, msg))
            else:
                content = response.content

    def consume(self):
        loop = True
        while loop:
            try:
                if self.channel is None:
                    raise pika.exceptions.ConnectionClosed()
                self.channel.start_consuming()
            except KeyboardInterrupt:
                loop = False
                self.channel.stop_consuming()
            except pika.exceptions.ConnectionClosed:
                try:
                    self.connect()
                except pika.exceptions.ConnectionClosed:
                    sleep(1)

        self.connection.close()


consumer = Consumer()
consumer.consume()
