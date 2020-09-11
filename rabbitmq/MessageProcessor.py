import jsonschema
import json
import logging

logger = logging.getLogger(__name__)


class MessageProcessor(object):
    """
    MessageProcessor describes the interface that all message processor classes should implement
    """
    schema = None       # override this in a subclass
    routing_key = None  # override this in a subclass

    def valid_message_receive(self, exchange_name, routing_key, delivery_tag, body):
        """
        override this method in a subclass in order to receive information
        :param exchange_name:
        :param routing_key:
        :param delivery_tag:
        :param body:
        :return:
        """
        logger.debug("Received validated message from {0} via {1} with {2}: {3}".format(exchange_name, routing_key, delivery_tag, body))
        pass

    def raw_message_receive(self, channel, method, properties, body):
        """
        called from the pika library when data is received on our channel.
        the implementation will attempt to decode the body as JSON and validate it using jsonschema against
        the schema provided by the `schema` member before passing it on to valid_message_receive
        normally you DON'T want to over-ride this, you want valid_message_receive
        :param channel:
        :param method:
        :param properties:
        :param body:
        :return:
        """
        tag = method.delivery_tag
        validated_content = None
        try:
            logger.debug("Received message with delivery tag {2} from {0}: {1}".format(channel, body.decode('UTF-8'), tag))
            unvalidated_content = json.loads(body.decode('UTF-8'))

            if self.schema:
                jsonschema.validate(unvalidated_content, self.schema)   # throws an exception if the content does not validate
            else:
                logger.warning("No schema present for validation in {0}, bad data might slip through".format(self.__class__.__name__))
            validated_content = unvalidated_content  #if we get to this line, then validation was successful
        except Exception as e:
            logger.exception("Message did not validate: ", exc_info=e)
            logger.error("Offending message content was {0}".format(body.decode('UTF-8')))
            channel.basic_nack(delivery_tag=tag, requeue=False)
            return

        if validated_content is not None:
            try:
                self.valid_message_receive(method.exchange, method.routing_key, method.delivery_tag, validated_content)
                channel.basic_ack(delivery_tag=tag)
            except Exception as e:
                logger.error("Could not process message: {0}".format(str(e)))
                channel.basic_nack(delivery_tag=tag, requeue=True)
