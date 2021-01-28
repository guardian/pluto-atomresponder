# coding: utf-8
from django.core.management.base import BaseCommand
from boto import kinesis, sts
from pprint import pprint
from time import sleep
import logging
import sys

logger = logging.getLogger(__name__)


class KinesisResponderBaseCommand(BaseCommand):
    """
    Base class for a Django command to run the responder.  Subclass this and:
     - set stream_name, role_name and session_name attributes
     - override startup_thread to provide an instance of your responder
    """
    args = ''
    help = 'runs the test kinesis responder'

    stream_name = 'stream name to connect to'
    role_name = 'ARN of role to use'
    session_name = 'session_name'

    def startup_thread(self, conn, shardinfo):
        """
        Override this method to start up a processing thread. This is called once for every shard in the stream
        :param conn: kinesis connection object
        :param shardinfo: dictionary of information about the shard, returned from describe_stream
        :return: a KinesisResponser subclass instance that will handle the messages for this shard
        """
        raise RuntimeError("startup_thread must be implemented in your subclass!")

    def handle(self, *args, **options):
        if 'aws_access_key_id' in options and 'aws_secret_access_key' in options:
            sts_conn = sts.connect_to_region('eu-west-1',
                                             aws_access_key_id=options['aws_access_key_id'],
                                             aws_secret_access_key=options['aws_secret_access_key'])
        else:
            sts_conn = sts.connect_to_region('eu-west-1')

        credentials = sts_conn.assume_role(self.role_name, self.session_name)

        conn = kinesis.connect_to_region('eu-west-1', aws_access_key_id=credentials.credentials.access_key,
                                         aws_secret_access_key=credentials.credentials.secret_key,
                                         security_token=credentials.credentials.session_token)

        streaminfo = conn.describe_stream(self.stream_name)

        threadlist = [self.startup_thread(credentials.credentials, shardinfo) for shardinfo in streaminfo['StreamDescription']['Shards']]

        logger.info("Stream {0} has {1} shards".format(self.stream_name,len(threadlist)))

        for t in threadlist:
            t.daemon = True
            t.start()

        print("Started up and processing. Hit CTRL-C to stop.", flush=True)
        #simplest way to allow ctrl-C when dealing with threads
        try:
            while True:
                sleep(60)
                for t in threadlist:
                    if not t.is_alive():
                        logger.error("A processing thread failed, exiting responder")
                        sys.exit(255)
        except KeyboardInterrupt:
            print("CTRL-C caught, cleaning up", flush=True)
