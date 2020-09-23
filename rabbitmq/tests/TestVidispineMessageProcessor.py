from django.test import TestCase
import os
from rabbitmq.VidispineMessageProcessor import VidispineMessageProcessor
from mock import MagicMock, patch
import pika
import json


class TestVidispineMessageProcessor(TestCase):
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
