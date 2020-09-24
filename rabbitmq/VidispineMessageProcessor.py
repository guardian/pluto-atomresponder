from .MessageProcessor import MessageProcessor
from .job_notification import JobNotification
import logging
from atomresponder.models import ImportJob
from kinesisresponder.sentry import inform_sentry_exception
from .transcode_check import check_for_broken_proxy, delete_existing_proxy, transcode_proxy
from datetime import datetime
import pytz
from django.conf import settings

logger = logging.getLogger(__name__)

time_zone: str = getattr(settings,"TIME_ZONE", "UTC")


class VidispineMessageProcessor(MessageProcessor):
    routing_key = "vidispine.job.essence_version.stop"
    # see https://json-schema.org/learn/miscellaneous-examples.html for more details
    schema = {
        "type": "object",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "properties": {
            "field": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/kvpair"
                }
            }
        },
        "definitions": {
            "kvpair": {
                "type": "object",
                "required": ["key","value"],
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                }
            }
        }
    }

    def valid_message_receive(self, exchange_name, routing_key, delivery_tag, body: dict):
        """
        receives the validated vidispine json message.
        :param exchange_name:
        :param routing_key:
        :param delivery_tag:
        :param body:
        :return:
        """
        logger.debug("got incoming message: ", body)
        notification = JobNotification(body)

        importjob = ImportJob.objects.get(job_id=notification.jobId)
        importjob.status = notification.status
        importjob.processing = False
        importjob.completed_at = datetime.now(tz=pytz.timezone(time_zone))
        importjob.save()

        if importjob.is_failed():
            VidispineMessageProcessor.handle_failed_job(importjob)
        else:
            try:
                logger.info("{0}: Checking for broken proxy".format(importjob.item_id))
                should_regen, shape_id = check_for_broken_proxy(importjob.item_id)
                if should_regen:
                    logger.info("{0}: Proxy needs regen. Existing shape id is {1}".format(importjob.item_id, shape_id))
                    if shape_id is not None:
                        logger.info("{0}: Deleting invalid proxy".format(importjob.item_id))
                        delete_existing_proxy(importjob.item_id, shape_id)
                    transcode_proxy(importjob.item_id, "lowres")
                else:
                    logger.info("{0}: Proxy is OK".format(importjob.item_id))
            except Exception as e:
                logger.exception("{0}: Could not do proxy check: ", exc_info=e)
                inform_sentry_exception()
        importjob.save()

    @staticmethod
    def handle_failed_job(import_job):
        """
        If the job failed, request a resend
        :param import_job: ImportJob model instance representing the failed job
        :return:
        """
        from atomresponder.media_atom import request_atom_resend
        from kinesisresponder.sentry import inform_sentry_exception
        max_retries = getattr(settings, "MAX_IMPORT_RETRIES", 10)

        logger.info("{0} ({1}): failed on attempt {2}".format(import_job.item_id, import_job.atom_id, import_job.retry_number))

        if import_job.retry_number > max_retries:
            logger.error("{0}: Have already retried {1} times, giving up".format(import_job.atom_id, import_job.retry_number))
            import_job.completed_at = datetime.now(tz=pytz.timezone(time_zone))
            import_job.status = "FAILED_TOTAL"
            import_job.processing = False
            import_job.save()
            return

        import_job.retry_number += 1
        import_job.save()

        try:
            logger.info("Requesting resend of atom {0}".format(import_job.atom_id))
            request_atom_resend(import_job.atom_id, settings.ATOM_TOOL_HOST, settings.ATOM_TOOL_SECRET)
            logger.info("Resend of atom {0} done".format(import_job.atom_id))
        except Exception as e:
            logger.error(e)
            inform_sentry_exception()
