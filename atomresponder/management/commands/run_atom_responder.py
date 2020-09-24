# coding: utf-8
from django.conf import settings
from atomresponder.master_importer import MasterImportResponder
from kinesisresponder.management.kinesis_responder_basecommand import KinesisResponderBaseCommand
import logging

logger = logging.getLogger(__name__)


class Command(KinesisResponderBaseCommand):
    stream_name = settings.INCOMING_KINESIS_STREAM
    role_name = settings.MEDIA_ATOM_ROLE_ARN

    session_name = "GNMAtomResponder"

    def handle(self, *args, **options):
        from kinesisresponder.sentry import inform_sentry_exception
        import traceback
        import xml.etree.cElementTree as ET
        from gnmvidispine.vs_external_id import ExternalIdNamespace
        from gnmvidispine.vidispine_api import VSNotFound

        #ensure that the namespace for our external IDs is present. If not, create it.
        #this is to make it simple for LaunchDetector to look up items by atom ID
        extid_namespace = ExternalIdNamespace(url=settings.VIDISPINE_URL,user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)
        try:
            extid_namespace.populate("atom_uuid")
            logger.info("Found external id namespace atom_uuid")
        except VSNotFound:
            try:
                extid_namespace.create("atom_uuid","[A-Fa-f0-9]{8}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{12}")
                logger.info("Created new external id namespace atom_uuid")
            except Exception as e:
                logger.error(traceback.format_exc())
                inform_sentry_exception(extra_ctx={'namespace_source': ET.tostring(extid_namespace._xmldoc, encoding="UTF-8")})
                raise

        newoptions = options.copy()
        newoptions.update({
            'aws_access_key_id': settings.MEDIA_ATOM_AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.MEDIA_ATOM_AWS_SECRET_ACCESS_KEY
        })

        super(Command, self).handle(*args,**newoptions)

    def startup_thread(self, conn, shardinfo):
        return MasterImportResponder(self.role_name,self.session_name,self.stream_name,shardinfo['ShardId'],
                                     aws_access_key_id=settings.MEDIA_ATOM_AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.MEDIA_ATOM_AWS_SECRET_ACCESS_KEY)