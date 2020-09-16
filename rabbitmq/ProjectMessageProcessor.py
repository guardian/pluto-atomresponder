import logging
from .MessageProcessor import MessageProcessor
from .media_atom import update_kinesis, MSG_PROJECT_CREATED, MSG_PROJECT_UPDATED
from .serializers import ProjectModelSerializer
from .models import ProjectModel, CachedCommission, LinkedProject
logger = logging.getLogger(__name__)


class ProjectMessageProcessor(MessageProcessor):
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

        project_model = ProjectModel(**body)
        try:
            cached_commission = CachedCommission.objects.get(id=project_model.commissionId)

            try:
                linked_project = LinkedProject.objects.get(project_id=project_model.id)
                linked_project.project_id = project_model.id
                linked_project.commission = cached_commission
                linked_project.save()
            except LinkedProject.DoesNotExist:
                linked_project = LinkedProject(project_id=project_model.id, commission=cached_commission)
                linked_project.save()

            logger.info("ProjectMessageProcessor got {0}".format(project_model))
            update_kinesis(project_model, cached_commission, message)
        except CachedCommission.DoesNotExist:
            logger.error("No cached commission data found for id {0}".format(project_model.commissionId))
            raise
