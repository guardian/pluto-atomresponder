from django.core.management.base import BaseCommand
import logging
import pika
from django.conf import settings
import re
from functools import partial
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs the responder program for in-cluster messages"

    @staticmethod
    def connect_channel(exchange_name, handler, channel):
        """
        async callback that is used to connect a channel once it has been declared
        :param channel: channel to set up
        :param exchange_name: str name of the exchange to connect to
        :param handler: a MessageProcessor class (NOT instance)
        :return:
        """
        logger.info("Establishing connection to exchange {0} from {1}...".format(exchange_name, handler.__class__.__name__))
        sanitised_routingkey = re.sub(r'[^\w\d]', '', handler.routing_key)

        queuename = "atomresponder-{0}".format(sanitised_routingkey)
        channel.exchange_declare(exchange=exchange_name, exchange_type="topic")
        channel.queue_declare(queuename)
        channel.queue_bind(queuename, exchange_name, routing_key=handler.routing_key)
        channel.basic_consume(queuename,
                              handler.raw_message_receive,
                              auto_ack=False,
                              exclusive=False,
                              callback=lambda consumer: logger.info("Consumer started for {0} from {1}".format(queuename, exchange_name))
                              )

    @staticmethod
    def channel_opened(connection):
        """
        async callback that is invoked when the connection is ready.
        it is used to connect up the channels
        :param connection: rabbitmq connection
        :return:
        """
        from rabbitmq.mappings import EXCHANGE_MAPPINGS
        logger.info("Connection opened")
        for i in range(0, len(EXCHANGE_MAPPINGS)):
            # partial adjusts the argument list, adding the args here onto the _start_ of the list
            # so the args are (exchange, handler, channel) not (channel, exchange, handler)
            connection.channel(on_open_callback=partial(Command.connect_channel,
                                                        EXCHANGE_MAPPINGS[i]["exchange"],
                                                        EXCHANGE_MAPPINGS[i]["handler"])
                               )

    @staticmethod
    def connection_closed(connection, error):
        """
        async callback that is invoked when the connection fails.
        print an error and shut down, this will then get detected as a crash-loop state
        :param connection:
        :param error:
        :return:
        """
        logger.error("RabbitMQ connection failed: {0}".format(str(error)))
        os.exit(1)

    def handle(self, *args, **options):
        import time
        connection = pika.SelectConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=getattr(settings, "RABBITMQ_PORT", 5672),
                virtual_host=getattr(settings, "RABBITMQ_VHOST", "/"),
                credentials=pika.PlainCredentials(username=settings.RABBITMQ_USER, password=settings.RABBITMQ_PASSWORD),
                connection_attempts=getattr(settings, "RABBITMQ_CONNECTION_ATTEMPTS", 50),
                retry_delay=getattr(settings, "RABBITMQ_RETRY_DELAY", 3)
            ),
            on_open_callback=Command.channel_opened,
        )

        # logger.info("Handling messages")
        # while True:
        #     time.sleep(3600)
        connection.ioloop.start()

