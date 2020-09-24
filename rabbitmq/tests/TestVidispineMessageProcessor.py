from django.test import TestCase
import os
from rabbitmq.VidispineMessageProcessor import VidispineMessageProcessor
from mock import MagicMock, patch
import pika
import json


class TestVidispineMessageProcessor(TestCase):
    fixtures = [
        "ImportJobs"
    ]

    @staticmethod
    def _get_test_data(filename):
        mypath = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(mypath, "data", filename)) as f:
            raw_content = f.read().encode('UTF-8')
            return raw_content

    def test_imports_data(self):
        """
        VidispineMessageProcessor should validate and hand off a correctly formatted server message to the valid_message_receive function
        :return:
        """
        content = self._get_test_data("samplemessage.json")
        toTest = VidispineMessageProcessor()
        toTest.valid_message_receive = MagicMock()

        mockChannel = MagicMock(target=pika.channel.Channel)
        mockDelivery = MagicMock(target=pika.spec.Tx)
        mockProps = MagicMock(target=pika.spec.BasicProperties)
        toTest.raw_message_receive(mockChannel,mockDelivery,mockProps, content)

        parsed_content = json.loads(content)

        toTest.valid_message_receive.assert_called_once()
        self.assertEqual(toTest.valid_message_receive.call_args.args[3], parsed_content)

    def test_process_notification_worked(self):
        """
        valid_message_receive should update the database with the status of the job that came back,
        and should NOT call handle_failed_job if there was no error
        :return:
        """
        from rabbitmq.job_notification import JobNotification
        from atomresponder.models import ImportJob
        from gnmvidispine.vs_item import VSItem
        mock_vsitem = MagicMock(target=VSItem)
        mock_vsitem.transcode = MagicMock(return_value="VX-888")

        content = self._get_test_data("samplemessage.json")
        parsed_content = json.loads(content)
        toTest = VidispineMessageProcessor()
        toTest.handle_failed_job = MagicMock()
        with patch("gnmvidispine.vs_item.VSItem", return_value=mock_vsitem) as VSItemFactory:
            with patch("rabbitmq.VidispineMessageProcessor.check_for_broken_proxy", return_value=(False, "VX-999")) as mock_check_proxy:
                data = JobNotification(parsed_content)
                before_record = ImportJob.objects.get(job_id=data.jobId)
                self.assertEqual(before_record.status,'STARTED')
                toTest.valid_message_receive("example_exchange","vidispine.job.essence_version.stop","1",parsed_content)
                after_record = ImportJob.objects.get(job_id=data.jobId)
                self.assertEqual(after_record.status,'FINISHED')
                toTest.handle_failed_job.assert_not_called()
                mock_check_proxy.assert_called_once_with(before_record.item_id)
