"""Simulate purge instructions"""
from time import sleep

import pika


parameters = pika.ConnectionParameters(
    "localhost", 5672, "/"
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange="purgatory", exchange_type="fanout")

loop = True
while loop:
    channel.basic_publish(
        exchange="purgatory",
        routing_key="",
        body="/some/path/"
    )
    sleep(2)

connection.close()
