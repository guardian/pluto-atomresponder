import logging
from .MessageProcessor import MessageProcessor
from .serializers import CachedCommissionSerializer
from .models import CachedCommission

logger = logging.getLogger(__name__)


class CommissionMessageProcessor(MessageProcessor):
    serializer = CachedCommissionSerializer
    routing_key = "core.commission.*"

    def valid_message_receive(self, exchange_name, routing_key, delivery_tag, body):
        logger.info("CommissionMessageProcessor got {0}".format(body))
        commission = CachedCommission(**body)
        if "create" in routing_key or "update" in routing_key:
            logger.info("Caching update commission '{0}' to database".format(commission.title))
            commission.save()
        elif "delete" in routing_key:   #check if this is the right key name
            logger.info("Removing deleted commission '{0}' from database".format(commission.title))
            commission.delete()
        else:
            logger.error("Unrecognised routing key: {0}".format(routing_key))