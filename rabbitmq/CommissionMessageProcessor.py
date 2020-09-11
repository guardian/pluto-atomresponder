import json
import logging
from .MessageProcessor import MessageProcessor

logger = logging.getLogger(__name__)

## see https://pynative.com/python-json-validation/
COMMISSION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},

    }
}


class CommissionMessageProcessor(MessageProcessor):
    schema = COMMISSION_SCHEMA
    routing_key = "core.commission.*"

    def valid_message_receive(self, exchange_name, routing_key, delivery_tag, body):
        logger.info("CommissionMessageProcessor got {0}".format(body))
