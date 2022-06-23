import logging
from .MessageProcessor import MessageProcessor
from .media_atom import update_kinesis, MSG_PROJECT_CREATED, MSG_PROJECT_UPDATED
from .serializers import ProjectModelSerializer
from .models import ProjectModel, CachedCommission, LinkedProject
import pika
from django.conf import settings
import json

logger = logging.getLogger(__name__)


def send_missing_commission_message(commission_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=getattr(settings, "RABBITMQ_PORT", 5672),
        virtual_host=getattr(settings, "RABBITMQ_VHOST", "/"),
        credentials=pika.PlainCredentials(username=settings.RABBITMQ_USER, password=settings.RABBITMQ_PASSWORD)
    ))
    channel = connection.channel()
    channel.queue_declare("missing-commissions", auto_delete=True)
    channel.queue_bind(exchange="pluto-atomresponder", queue="missing-commissions",
                       routing_key="atomresponder.commission.missing-id")
    logger.info("About to send commission missing id. message for commission: {0}.".format(commission_id))
    channel.basic_publish(exchange="pluto-atomresponder",
                          routing_key="atomresponder.commission.missing-id",
                          body='{"id":"%s"}' % commission_id)


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
            send_missing_commission_message(project_model.commissionId)
            logger.warning("No cached commission data found for id {0}".format(project_model.commissionId))
            raise

    def raw_message_receive(self, channel, method, properties, body):
        tag = method.delivery_tag
        validated_content = None
        try:
            if self.serializer:
                validated_content = self.validate_with_serializer(body)
            elif self.schema:
                validated_content = self.validate_with_schema(body)
            else:
                logger.warning("No schema nor serializer resent for validation in {0}, cannot continue".format(self.__class__.__name__))
                channel.basic_nack(delivery_tag=tag, requeue=True)

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
                channel.basic_nack(delivery_tag=tag, requeue=False)
                body_data = json.loads(body.decode('UTF-8'))[0]
                should_retry = True
                if "retry_count" in body_data:
                    if body_data["retry_count"] > 32:
                        should_retry = False
                if should_retry:
                    if "retry_count" in body_data:
                        body_data["retry_count"] = body_data["retry_count"] + 1
                    else:
                        body_data["retry_count"] = 1
                    body_as_json = json.dumps([body_data]).encode('UTF-8')
                    logger.info("Publishing the message again with a retry count of {0} on exchange {1} with key {2}".format(body_data["retry_count"], method.exchange, method.routing_key))
                    try:
                        channel.basic_publish(exchange=method.exchange, routing_key=method.routing_key, body=body_as_json, properties=properties)
                    except Exception as e:
                        logger.error("Could not publish message: {0}".format(str(e)))
                else:
                    logger.info("Publishing the message again with a retry count of {0} on exchange atomresponder-dlx with key atomresponder-dlq".format(body_data["retry_count"]))
                    channel.basic_publish(exchange="atomresponder-dlx", routing_key="atomresponder-dlq", body=body, properties=properties)
        else:
            logger.error("Validated content was empty but no validation error? There must be a bug")
            channel.basic_nack(delivery_tag=tag, requeue=True)
            channel.basic_cancel(method.consumer_tag)
            raise ValueError("Validated content empty but no validation error")
