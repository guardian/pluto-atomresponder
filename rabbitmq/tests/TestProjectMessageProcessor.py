from django.test import TestCase
from rabbitmq.ProjectMessageProcessor import ProjectMessageProcessor, CachedCommission
from rabbitmq.models import ProjectModel
from mock import MagicMock, patch
from collections import OrderedDict
import datetime
import pytz


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
            project_id=1234,
            project_type_id=1,
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
        update
        :return:
        """
        data = OrderedDict(
            project_id=1234,
            project_type_id=1,
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
            to_test.valid_message_receive("my_exchange","core.project.update","sometag",data)

            mock_update_kinesis.assert_called_once_with(ProjectModel(**data), expected_commission, "project-updated")

    def test_invalid(self):
        """
        ProjectMessageProcessor should not call out to update_kinesis if the routing key is not crete nor update, but
        instead raise a ValueError
        :return:
        """
        data = OrderedDict(
            project_id=1234,
            project_type_id=1,
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
        ProjectMessageProcessor should re-raise an exception if the commission id is not valid and not call out
        to update_kinesis
        :return:
        """
        data = OrderedDict(
            project_id=1234,
            project_type_id=1,
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
            to_test = ProjectMessageProcessor()
            with self.assertRaises(CachedCommission.DoesNotExist):
                to_test.valid_message_receive("my_exchange","core.project.create","sometag",data)

            mock_update_kinesis.assert_not_called()