import json
import logging
from .MessageProcessor import MessageProcessor
from atomresponder.media_atom import update_kinesis, MSG_PROJECT_CREATED, MSG_PROJECT_UPDATED
from .serializers import ProjectModelSerializer
logger = logging.getLogger(__name__)

## see https://pynative.com/python-json-validation/
PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "projectTypeId": {"type": "number"},
        "title": {"type": "string"},
        "created": {"type": "string"},
        "user": {"type": "string"},
        "workingGroupId": {"type": "string"},
        "commissionId": {"type": "string"},
        "deletable": {"type": "boolean"},
        "sensitive": {"type": "boolean"},
        "status": {"type": "string"},
        "productionOffice": {"type": "string"},
    }
}


class ProjectMessageProcessor(MessageProcessor):
    #schema = PROJECT_SCHEMA
    serializer = ProjectModelSerializer
    routing_key = "core.project.*"

    def valid_message_receive(self, exchange_name, routing_key, delivery_tag, body):
        message = None
        if "create" in routing_key:
            logger.debug("Received project created message")
            message = MSG_PROJECT_CREATED
        elif "update" in routing_key:
            logger.debug("Received project update message")
            message = MSG_PROJECT_UPDATED
        else:
            logger.error("Received unknown message of type {0}".format(routing_key))
            raise ValueError("Unknown routing key")

        logger.info("ProjectMessageProcessor got {0}".format(body))
        update_kinesis(project_model, MSG_PROJECT_CREATED)