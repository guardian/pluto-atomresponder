from kinesisresponder.kinesis_responder import KinesisResponder
import json
import urllib.request, urllib.parse, urllib.error
from django.conf import settings
from .s3_mixin import S3Mixin, FileDoesNotExist
from .vs_mixin import VSMixin
import logging
from gnmvidispine.vs_item import VSItem, VSNotFound
from rabbitmq.models import LinkedProject
from datetime import datetime
import atomresponder.constants as const
import re
import pika
import time
import os
import posix

logger = logging.getLogger(__name__)

#Still need: holding image. this is more likely to come from the launch detection side than the atom side.

extract_extension = re.compile(r'^(?P<basename>.*)\.(?P<extension>[^\.]+)$')
multiple_underscore_re = re.compile(r'_{2,}')
make_filename_re = re.compile(r'[^\w\d\.]')


class MasterImportResponder(KinesisResponder, S3Mixin, VSMixin):
    def __init__(self, *args, **kwargs):
        super(MasterImportResponder, self).__init__(*args, **kwargs)
        self._pika_client = None

    @staticmethod
    def setup_pika_channel() -> (pika.spec.Connection, pika.spec.Channel):
        conn = pika.BlockingConnection(pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=getattr(settings, "RABBITMQ_PORT", 5672),
            virtual_host=getattr(settings, "RABBITMQ_VHOST", "/"),
            credentials=pika.PlainCredentials(username=settings.RABBITMQ_USER, password=settings.RABBITMQ_PASSWORD),
            connection_attempts=getattr(settings, "RABBITMQ_CONNECTION_ATTEMPTS", 3),
            retry_delay=getattr(settings, "RABBITMQ_RETRY_DELAY", 3)
        ))

        channel = conn.channel()
        channel.exchange_declare(settings.RABBITMQ_EXCHANGE, exchange_type="topic")
        channel.confirm_delivery()

        return conn, channel

    def update_pluto_record(self, item_id, job_id, content:dict, statinfo):
        (conn, channel) = self.setup_pika_channel()

        if 'type' not in content:
            logger.error("Content dictionary had no type information! Using video-upload")
            type = const.MESSAGE_TYPE_MEDIA
        else:
            type = content['type']

        routingkey = "atomresponder.atom.{}".format(type)

        try:
            linked_project = LinkedProject.objects.get(project_id=int(content['projectId']))
            commission_id = linked_project.commission.id
        except ValueError:
            logger.error("Project ID {} does not convert to integer!".format(content['projectId']))
            commission_id = -1
        except KeyError:
            logger.error("Content has no projectId? invalid message.")
            raise RuntimeError("Invalid message")
        except LinkedProject.DoesNotExist:
            commission_id = -1

        if statinfo is not None:
            statpart = {
                "size": statinfo.st_size,
                "atime": statinfo.st_atime,
                "mtime": statinfo.st_mtime,
                "ctime": statinfo.st_ctime
            }
        else:
            statpart = {}

        message_to_send = {
            **content,
            "itemId": item_id,
            "jobId": job_id,
            "commissionId": commission_id,
            **statpart
        }

        while True:
            try:
                logger.info("Updating exchange {} with routing-key {}...".format(settings.RABBITMQ_EXCHANGE, routingkey))
                channel.basic_publish(settings.RABBITMQ_EXCHANGE, routingkey, json.dumps(message_to_send).encode("UTF-8"))
                conn.close()    #makes sure everything gets flushed nicely
                break
            except pika.exceptions.UnroutableError:
                logger.error("Could not route message to broker, retrying in 3s...")
                time.sleep(3)

    def get_or_create_master_item(self, atomId:str, title:str, filename:str, project_id:int, user:str) -> (VSItem, bool):
        master_item = self.get_item_for_atomid(atomId)

        created = False

        if master_item is None:
            if title is None:
                raise ValueError("Title field not set for atom {0}.".format(atomId))
            if user is None:
                logger.warning("User field not set for atom {0}.".format(atomId))
                user_to_set="unknown_user"
            else:
                user_to_set=user
            master_item = self.create_placeholder_for_atomid(atomId,
                                                             filename=filename,
                                                             title=title,
                                                             project_id=project_id,
                                                             user=user_to_set)
            logger.info("Created item {0} for atom {1}".format(master_item.name, atomId))
            created = True
        return master_item, created

    def process(self,record, approx_arrival, attempt=0):
        """
        Process a message from the kinesis stream.  Each record is a JSON document which contains keys for atomId, s3Key,
        projectId.  This will find an item with the given atom ID or create a new one, get a signed download URL from
        S3 for the media and then instruct Vidsipine to import it.
        Rather than wait for the job to complete here, we return immediately and rely on receiving a message from VS
        when the job terminates.
        :param record: JSON document in the form of a string
        :param approx_arrival:
        :param attempt: optional integer showing how many times this has been retried
        :return:
        """
        from .media_atom import request_atom_resend, HttpError
        content = json.loads(record)

        logger.info(content)

        #We get two types of message on the stream, one for incoming xml the other for incoming media.
        if content['type'] == const.MESSAGE_TYPE_MEDIA or content['type'] == const.MESSAGE_TYPE_RESYNC_MEDIA:
            if 'user' in content:
                atom_user = content['user']
            else:
                atom_user = None
            master_item, created = self.get_or_create_master_item(content['atomId'],
                                                                  title=content['title'],
                                                                  filename=content['s3Key'],
                                                                  project_id=content['projectId'],
                                                                  user=atom_user)

            return self.import_new_item(master_item, content)
        elif content['type'] == const.MESSAGE_TYPE_PAC:
            logger.info("Got PAC form data message")
            record = self.register_pac_xml(content)
            self.ingest_pac_xml(record)
            logger.info("PAC form data message complete")
        elif content['type'] == const.MESSAGE_TYPE_PROJECT_ASSIGNED:
            logger.info("Got project (re-)assignment message: {0}".format(content))

            master_item = self.get_item_for_atomid(content['atomId'])
            if master_item is not None:
                logger.info("Master item for atom already exists at {0}, assigning".format(master_item.name))
                self.update_pluto_record(master_item.name, None, content, None)
            else:
                logger.warning("No master item exists for atom {0}.  Requesting a re-send from media atom tool".format(content['atomId']))
                try:
                    request_atom_resend(content['atomId'], settings.ATOM_TOOL_HOST, settings.ATOM_TOOL_SECRET)
                except HttpError as e:
                    if e.code == 404:
                        if attempt >= 10:
                            logger.error("{0}: still nothing after 10 attempts. Giving up.".format(content['atomId']))
                            raise
                        logger.warning("{0}: Media atom tool responded with a 404 on attempt {1}: {2}. Retry is NOT YET IMPLEMENTED.".format(content['atomId'], attempt, e.content))
                        # timed_request_resend.apply_async(args=(record, approx_arrival),
                        #                                  kwargs={'attempt': attempt+1},
                        #                                  countdown=60)
                    else:
                        logger.exception("{0}: Could not request resync".format(content['atomId']))

            logger.info("Project (re-)assignment complete")
        else:
            raise ValueError("Unrecognised message type: {0}".format(content['type']))

    def register_pac_xml(self, content):
        """
        Start the import of new PAC data by registering it in the database.
        :param content: JSON message content as received from atom tool
        :return: the database model instance
        """
        from .models import PacFormXml

        (record, created) = PacFormXml.objects.get_or_create(atom_id=content['atomId'], defaults={'received': datetime.now()})
        if not created:
            logger.info("PAC form xml had already been delivered for {0}, over-writing".format(content['atomId']))

        record.completed = None
        record.status = "UNPROCESSED"
        record.last_error = ""
        record.pacdata_url = "s3://{bucket}/{path}".format(bucket=content['s3Bucket'], path=content['s3Path'])
        record.save()
        return record

    def check_for_old_finished_jobs(self, vs_item_id):
        from .models import ImportJob

        jobs = ImportJob.objects.filter(item_id=vs_item_id).filter(status='FINISHED').count()

        return jobs > 0

    def check_key(self, key, vs_item_id):
        from .models import ImportJob

        jobs = ImportJob.objects.filter(item_id=vs_item_id).filter(s3_path=key).count()

        return jobs > 0

    def check_for_processing(self, vs_item_id):
        from .models import ImportJob

        jobs = ImportJob.objects.filter(item_id=vs_item_id).filter(processing=True).count()

        return jobs > 0

    def import_new_item(self, master_item:VSItem, content):
        from .models import ImportJob, PacFormXml
        from .pac_xml import PacXmlProcessor
        from mock import MagicMock
        if not isinstance(master_item, VSItem) and not isinstance(master_item, MagicMock): raise TypeError #for intellij
        from kinesisresponder.sentry import inform_sentry

        vs_item_id = master_item.get("itemId")

        if vs_item_id is None:
            vs_item_id = master_item.name

        old_finished_jobs = self.check_for_old_finished_jobs(vs_item_id)

        old_key = self.check_key(content['s3Key'], vs_item_id)

        if old_finished_jobs is True and old_key is True:
            logger.info('A job for item {0} has already been successfully completed. Aborting.'.format(vs_item_id))
            inform_sentry('A job for item {0} has already been successfully completed. Aborting.'.format(vs_item_id), {
                "master_item": master_item,
                "content": content,
            })
            return

        processing_job = self.check_for_processing(vs_item_id)

        if processing_job is True:
            logger.info('Job for item {0} already in progress. Aborting.'.format(vs_item_id))
            inform_sentry('Job for item {0} already in progress. Aborting.'.format(vs_item_id), {
                "master_item": master_item,
                "content": content,
            })
            return

        safe_title = content.get('title','(unknown title)').encode("UTF-8","backslashescape").decode("UTF-8")

        #using a signed URL is preferred, but right now VS seems to have trouble ingesting it.
        #so, we download instead and ingest that. get_s3_signed_url is left in to make it simple to switch back
        #download_url = self.get_s3_signed_url(bucket=settings.ATOM_RESPONDER_DOWNLOAD_BUCKET, key=content['s3Key'])
        downloaded_path = self.download_to_local_location(bucket=settings.ATOM_RESPONDER_DOWNLOAD_BUCKET,
                                                          key=content['s3Key'],
                                                          #this is converted to a safe filename within download_to_local_location
                                                          filename=content.get('title', None)) #filename=None => use s3key instead

        download_url = "file://" + urllib.parse.quote(downloaded_path)

        logger.info("{n}: Ingesting atom with title '{0}' from media atom with ID {1}".format(safe_title,
                                                                                              content['atomId'],
                                                                                              n=master_item.name))

        logger.info("{n}: Download URL is {0}".format(download_url, n=master_item.name))

        job_result = master_item.import_to_shape(uri=download_url,
                                                 essence=True,
                                                 shape_tag=getattr(settings,"ATOM_RESPONDER_SHAPE_TAG","lowres"),
                                                 priority=getattr(settings,"ATOM_RESPONDER_IMPORT_PRIORITY","HIGH"),
                                                 jobMetadata={'gnm_source': 'media_atom'},
                                                 )
        logger.info("{0} Import job is at ID {1}".format(vs_item_id, job_result.name))

        #make a note of the record. This is to link it up with Vidispine's response message.
        record = ImportJob(item_id=vs_item_id,
                           job_id=job_result.name,
                           status='STARTED',
                           started_at=datetime.now(),
                           user_email=content.get('user',"Unknown user"),
                           atom_id=content['atomId'],
                           atom_title=content.get('title', "Unknown title"),
                           s3_path=content['s3Key'],
                           processing=True)
        previous_attempt = record.previous_attempt()
        if previous_attempt:
            record.retry_number = previous_attempt.retry_number+1
            logger.info("{0} Import job is retry number {1}".format(vs_item_id, record.retry_number))
        record.save()

        statinfo = os.stat(downloaded_path)

        self.update_pluto_record(vs_item_id, job_result.name, content, statinfo)

        try:
            logger.info("{n}: Looking for PAC info that has been already registered".format(n=vs_item_id))
            pac_entry = PacFormXml.objects.get(atom_id=content['atomId'])
            logger.info("{n}: Found PAC form information at {0}".format(pac_entry.pacdata_url,n=vs_item_id))
            proc = PacXmlProcessor(self.role_name, self.session_name)
            proc.link_to_item(pac_entry, master_item)
        except PacFormXml.DoesNotExist:
            logger.info("{n}: No PAC form information has yet arrived".format(n=vs_item_id))
        
    def ingest_pac_xml(self, pac_xml_record):
        """
        Master process to perform import of pac data
        :param pac_xml_record: instance of PacFormXml model
        :return:
        """
        from .pac_xml import PacXmlProcessor

        vsitem = self.get_item_for_atomid(pac_xml_record.atom_id)
        if vsitem is None:
            logger.warning("No item could be found for atom ID {0}, waiting for it to arrive".format(pac_xml_record.atom_id))
            return

        proc = PacXmlProcessor(self.role_name,self.session_name)

        #this process will call out to Pluto to do the linkup once the data has been received
        return proc.link_to_item(pac_xml_record, vsitem)