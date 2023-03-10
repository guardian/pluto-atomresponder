from django.test import TestCase
from rabbitmq.MessageProcessor import MessageProcessor
from rabbitmq.serializers import CachedCommissionSerializer
from mock import MagicMock, patch
from collections import OrderedDict
import pika

class TestMessageProcessorRawReceive(TestCase):
    def test_raw_receieve_valid_commissiondata(self):
        """
        on receiving data, raw_receive should validate it with the given serializer then call
        valid_message_receive to process it; if this returns successfully it should ack the message to the server
        :return:
        """
        class TestProcessor(MessageProcessor):
            serializer = CachedCommissionSerializer

        to_test = TestProcessor()
        to_test.valid_message_receive = MagicMock()

        mock_channel = MagicMock(target=pika.channel.Channel)
        mock_method = MagicMock(target=pika.spec.Basic.Deliver)
        mock_method.exchange = "exchange_name"
        mock_method.delivery_tag = "deltag"
        mock_method.routing_key = "routing.key"
        mock_properties = {}
        mock_content = b"""[{"id":12345,"title":"Some title"}]"""

        to_test.raw_message_receive(mock_channel, mock_method, mock_properties, mock_content)
        to_test.valid_message_receive.assert_called_once_with("exchange_name",
                                                              "routing.key",
                                                              "deltag",
                                                              OrderedDict([('id', 12345), ('title', 'Some title')])
                                                              )
        mock_channel.basic_nack.assert_not_called()
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="deltag")

    def test_raw_receieve_invalid_commissiondata(self):
        """
        on receiving data, raw_receive should validate it with the given serializer nack the message
        without redelivery if it fails to validate
        :return:
        """
        class TestProcessor(MessageProcessor):
            serializer = CachedCommissionSerializer

        to_test = TestProcessor()
        to_test.valid_message_receive = MagicMock()

        mock_channel = MagicMock(target=pika.channel.Channel)
        mock_method = MagicMock(target=pika.spec.Basic.Deliver)
        mock_method.exchange = "exchange_name"
        mock_method.delivery_tag = "deltag"
        mock_method.routing_key = "routing.key"
        mock_properties = {}
        mock_content = b"""{"commisid":12345,"title":"Some title"}"""

        to_test.raw_message_receive(mock_channel, mock_method, mock_properties, mock_content)
        to_test.valid_message_receive.assert_not_called()
        mock_channel.basic_ack.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="deltag", requeue=False)

    def test_raw_receieve_processingerror(self):
        """
        on receiving data, raw_receive should validate it with the given serializer then call
        valid_message_receive to process it; if this fails then it should nack the message with requeue
        :return:
        """
        class TestProcessor(MessageProcessor):
            serializer = CachedCommissionSerializer

        to_test = TestProcessor()
        to_test.valid_message_receive = MagicMock(side_effect=ValueError("too slow!"))

        mock_channel = MagicMock(target=pika.channel.Channel)
        mock_method = MagicMock(target=pika.spec.Basic.Deliver)
        mock_method.exchange = "exchange_name"
        mock_method.delivery_tag = "deltag"
        mock_method.routing_key = "routing.key"
        mock_properties = {}
        mock_content = b"""{"id":12345,"title":"Some title","junk_field":"junk"}"""

        with self.assertRaises(ValueError):
            to_test.raw_message_receive(mock_channel, mock_method, mock_properties, mock_content)
            to_test.valid_message_receive.assert_called_once_with("exchange_name",
                                                                  "routing.key",
                                                                  "deltag",
                                                                  OrderedDict([('id', 12345), ('title', 'Some title')])
                                                                  )
            mock_channel.basic_ack.assert_not_called()
            mock_channel.basic_nack.assert_called_once_with(delivery_tag="deltag", requeue=True)