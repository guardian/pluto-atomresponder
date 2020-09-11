import json
import logging
from .MessageProcessor import MessageProcessor

logger = logging.getLogger(__name__)

# interface Project {
#     id: number;
# projectTypeId: number;
# title: string;
# created: string;
# user: string;
# workingGroupId: number;
# commissionId: number;
# deletable: boolean;
# deep_archive: boolean;
# sensitive: boolean;
# status: ProjectStatus;
# productionOffice: ProductionOffice;
# }

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


class PlutoCoreMessageProcessor(MessageProcessor):
    schema = PROJECT_SCHEMA
    routing_key = "core.project.*"

    def valid_message_receive(self, exchange_name, routing_key, delivery_tag, body):
        logger.info("PlutoCoreMessageProcessor got {0}".format(body))
