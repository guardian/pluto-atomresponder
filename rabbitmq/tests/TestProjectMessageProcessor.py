from django.test import TestCase
from rabbitmq.ProjectMessageProcessor import ProjectMessageProcessor, CachedCommission, LinkedProject
from rabbitmq.models import ProjectModel
from mock import MagicMock, patch
from collections import OrderedDict
import datetime
import pytz
from rabbitmq.serializers import ProjectModelSerializer
import pika


class TestProjectMessageProcessor(TestCase):
    fixtures = [
        "CachedCommissions.yaml"
    ]

    def test_normal(self):
        """
        ProjectMessageProcessor should look up the associated commission and call out to update_kinesis with a new
        data record if the key is "create"
        :return:
        """
        data = OrderedDict(
            id=1234,
            projectTypeId=1,
            title="Some project title",
            created=datetime.datetime(2020,1,2,3,4,5,tzinfo=pytz.UTC),
            user="Fred",
            workingGroupId=5,
            commissionId=1,
            deletable=False,
            sensitive=False,
            status="In Production",
            productionOffice="UK"
        )

        expected_commission = CachedCommission.objects.get(pk=1)

        with patch("rabbitmq.ProjectMessageProcessor.update_kinesis") as mock_update_kinesis:
            to_test = ProjectMessageProcessor()
            to_test.valid_message_receive("my_exchange","core.project.create","sometag",data)

            mock_update_kinesis.assert_called_once_with(ProjectModel(**data), expected_commission, "project-created")

    def test_update(self):
        """
        ProjectMessageProcessor should look up the associated commission and call out to update_kinesis with an
        update having cached the project link record
        :return:
        """
        data = OrderedDict(
            id=1234,
            projectTypeId=1,
            title="Some project title",
            created=datetime.datetime(2020,1,2,3,4,5,tzinfo=pytz.UTC),
            user="Fred",
            workingGroupId=5,
            commissionId=1,
            deletable=False,
            sensitive=False,
            status="In Production",
            productionOffice="UK"
        )

        expected_commission = CachedCommission.objects.get(pk=1)

        with self.assertRaises(LinkedProject.DoesNotExist):
            LinkedProject.objects.get(project_id=1234)

        with patch("rabbitmq.ProjectMessageProcessor.update_kinesis") as mock_update_kinesis:
            to_test = ProjectMessageProcessor()
            to_test.valid_message_receive("my_exchange","core.project.update","sometag",data)

            mock_update_kinesis.assert_called_once_with(ProjectModel(**data), expected_commission, "project-updated")
            linked_project = LinkedProject.objects.get(project_id=1234)
            self.assertEqual(linked_project.commission.id, data["commissionId"])

    def test_invalid(self):
        """
        ProjectMessageProcessor should not call out to update_kinesis if the routing key is not crete nor update, but
        instead raise a ValueError
        :return:
        """
        data = OrderedDict(
            id=1234,
            projectTypeId=1,
            title="Some project title",
            created=datetime.datetime(2020,1,2,3,4,5,tzinfo=pytz.UTC),
            user="Fred",
            workingGroupId=5,
            commissionId=1,
            deletable=False,
            sensitive=False,
            status="In Production",
            productionOffice="UK"
        )

        with patch("rabbitmq.ProjectMessageProcessor.update_kinesis") as mock_update_kinesis:
            to_test = ProjectMessageProcessor()
            with self.assertRaises(ValueError):
                to_test.valid_message_receive("my_exchange","core.project.delete","sometag",data)

            mock_update_kinesis.assert_not_called()

    def test_invalid_comm(self):
        """
        ProjectMessageProcessor should attempt to send a message if the commission id. is not valid
        :return:
        """
        data = OrderedDict(
            id=1234,
            projectTypeId=1,
            title="Some project title",
            created=datetime.datetime(2020,1,2,3,4,5,tzinfo=pytz.UTC),
            user="Fred",
            workingGroupId=5,
            commissionId=5,
            deletable=False,
            sensitive=False,
            status="In Production",
            productionOffice="UK"
        )

        with patch("rabbitmq.ProjectMessageProcessor.update_kinesis") as mock_update_kinesis:
            with patch("rabbitmq.ProjectMessageProcessor.send_missing_commission_message") as mock_send_missing_commission_message:
                to_test = ProjectMessageProcessor()
                with self.assertRaises(CachedCommission.DoesNotExist):
                    to_test.valid_message_receive("my_exchange", "core.project.create", "sometag", data)

                mock_update_kinesis.assert_not_called()
                mock_send_missing_commission_message.assert_called_once_with(5)

    def test_raw_receive_with_exception(self):
        """
        If an exception is thrown when attempting to process the data a new message should be published which includes the tag 'retry_count'.
        :return:
        """
        class TestProcessor(ProjectMessageProcessor):
            serializer = ProjectModelSerializer

        to_test = TestProcessor()
        to_test.valid_message_receive = MagicMock()
        to_test.valid_message_receive.side_effect = Exception()

        mock_channel = MagicMock(target=pika.channel.Channel)
        mock_method = MagicMock(target=pika.spec.Basic.Deliver)
        mock_method.exchange = "exchange_name"
        mock_method.delivery_tag = "deltag"
        mock_method.routing_key = "routing.key"
        mock_properties = {}
        mock_content = b"""{"id":12345,"title":"Some title","projectTypeId":1,"created":"2022-06-17T11:11","user":"Fred","workingGroupId":5,"commissionId":5,"deletable":false,"sensitive":false,"status":"In Production","productionOffice":"UK"}"""

        with self.assertRaises(ValueError):
            to_test.raw_message_receive(mock_channel, mock_method, mock_properties, mock_content)
        mock_channel.basic_ack.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="deltag")
        mock_channel.basic_publish.assert_called_once_with(body=b'{"id": 12345, "title": "Some title", "projectTypeId": 1, "created": "2022-06-17T11:11", "user": "Fred", "workingGroupId": 5, "commissionId": 5, "deletable": false, "sensitive": false, "status": "In Production", "productionOffice": "UK", "retry_count": 1}', exchange='exchange_name', properties={}, routing_key='routing.key')

    def test_raw_receive_with_more_than_one_retry(self):
        """
        If an exception is thrown when attempting to process the data a new message should be published which includes the tag 'retry_count' with its value to set to one above the old value.
        :return:
        """
        class TestProcessor(ProjectMessageProcessor):
            serializer = ProjectModelSerializer

        to_test = TestProcessor()
        to_test.valid_message_receive = MagicMock()
        to_test.valid_message_receive.side_effect = Exception()

        mock_channel = MagicMock(target=pika.channel.Channel)
        mock_method = MagicMock(target=pika.spec.Basic.Deliver)
        mock_method.exchange = "exchange_name"
        mock_method.delivery_tag = "deltag"
        mock_method.routing_key = "routing.key"
        mock_properties = {}
        mock_content = b"""{"id":12345,"title":"Some title","projectTypeId":1,"created":"2022-06-17T11:11","user":"Fred","workingGroupId":5,"commissionId":5,"deletable":false,"sensitive":false,"status":"In Production","productionOffice":"UK","retry_count":23}"""

        with self.assertRaises(ValueError):
            to_test.raw_message_receive(mock_channel, mock_method, mock_properties, mock_content)
        mock_channel.basic_ack.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="deltag")
        mock_channel.basic_publish.assert_called_once_with(body=b'{"id": 12345, "title": "Some title", "projectTypeId": 1, "created": "2022-06-17T11:11", "user": "Fred", "workingGroupId": 5, "commissionId": 5, "deletable": false, "sensitive": false, "status": "In Production", "productionOffice": "UK", "retry_count": 24}', exchange='exchange_name', properties={}, routing_key='routing.key')

    def test_raw_receive_with_two_many_reties(self):
        """
        If an exception is thrown when attempting to process the data and there have already been thirty two retries for the message, the message should be published to the dead letter exchange.
        :return:
        """
        class TestProcessor(ProjectMessageProcessor):
            serializer = ProjectModelSerializer

        to_test = TestProcessor()
        to_test.valid_message_receive = MagicMock()
        to_test.valid_message_receive.side_effect = Exception()

        mock_channel = MagicMock(target=pika.channel.Channel)
        mock_method = MagicMock(target=pika.spec.Basic.Deliver)
        mock_method.exchange = "exchange_name"
        mock_method.delivery_tag = "deltag"
        mock_method.routing_key = "routing.key"
        mock_properties = {}
        mock_content = b"""{"id":12345,"title":"Some title","projectTypeId":1,"created":"2022-06-17T11:11","user":"Fred","workingGroupId":5,"commissionId":5,"deletable":false,"sensitive":false,"status":"In Production","productionOffice":"UK","retry_count":34}"""

        with self.assertRaises(ValueError):
            to_test.raw_message_receive(mock_channel, mock_method, mock_properties, mock_content)
        mock_channel.basic_ack.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="deltag")
        mock_channel.basic_publish.assert_called_once_with(body=b'{"id":12345,"title":"Some title","projectTypeId":1,"created":"2022-06-17T11:11","user":"Fred","workingGroupId":5,"commissionId":5,"deletable":false,"sensitive":false,"status":"In Production","productionOffice":"UK","retry_count":34}', exchange='atomresponder-dlx', properties={}, routing_key='routing.key')
