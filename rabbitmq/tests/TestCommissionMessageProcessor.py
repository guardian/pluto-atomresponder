from django.test import TestCase
from rabbitmq.CommissionMessageProcessor import CommissionMessageProcessor
from rabbitmq.models import CachedCommission
from mock import MagicMock, patch
from collections import OrderedDict


class TestCommissionMessageProcessor(TestCase):
    def test_create_message(self):
        """
        commissionMessageProcessor should save the provided model instance if the routing key is a ".create" one
        :return:
        """
        mock_body = OrderedDict([("id",1234),("title","Rhubarb")])
        mock_model = MagicMock(target=CachedCommission)
        mock_model.save = MagicMock()
        mock_model.delete = MagicMock()

        with patch("rabbitmq.CommissionMessageProcessor.CachedCommission", return_value=mock_model) as mock_factory:
            to_test = CommissionMessageProcessor()
            to_test.valid_message_receive("my_exchange","core.commission.create","sometag",mock_body)
            mock_factory.assert_called_once_with(id=1234,title="Rhubarb")
            mock_model.save.assert_called_once_with()
            mock_model.delete.assert_not_called()

    def test_update_message(self):
        """
        commissionMessageProcessor should save the provided model instance if the routing key is a ".update" one
        :return:
        """
        mock_body = OrderedDict([("id",1234),("title","Rhubarb")])
        mock_model = MagicMock(target=CachedCommission)
        mock_model.save = MagicMock()
        mock_model.delete = MagicMock()

        with patch("rabbitmq.CommissionMessageProcessor.CachedCommission", return_value=mock_model) as mock_factory:
            to_test = CommissionMessageProcessor()
            to_test.valid_message_receive("my_exchange","core.commission.update","sometag",mock_body)
            mock_factory.assert_called_once_with(id=1234,title="Rhubarb")
            mock_model.save.assert_called_once_with()
            mock_model.delete.assert_not_called()

    def test_delete_message(self):
        """
        commissionMessageProcessor should delete the provided model instance if the routing key is a ".delete" one
        :return:
        """
        mock_body = OrderedDict([("id",1234),("title","Rhubarb")])
        mock_model = MagicMock(target=CachedCommission)
        mock_model.save = MagicMock()
        mock_model.delete = MagicMock()

        with patch("rabbitmq.CommissionMessageProcessor.CachedCommission", return_value=mock_model) as mock_factory:
            to_test = CommissionMessageProcessor()
            to_test.valid_message_receive("my_exchange","core.commission.delete","sometag",mock_body)
            mock_factory.assert_called_once_with(id=1234,title="Rhubarb")
            mock_model.save.assert_not_called()
            mock_model.delete.assert_called_once_with()

    def test_unknown_message(self):
        """
        commissionMessageProcessor should neither save nor delete the provided model instance if the
         routing key is not recognised
        :return:
        """
        mock_body = OrderedDict([("id",1234),("title","Rhubarb")])
        mock_model = MagicMock(target=CachedCommission)
        mock_model.save = MagicMock()
        mock_model.delete = MagicMock()

        with patch("rabbitmq.CommissionMessageProcessor.CachedCommission", return_value=mock_model) as mock_factory:
            to_test = CommissionMessageProcessor()
            to_test.valid_message_receive("my_exchange","core.commission.fdsfsfsg","sometag",mock_body)
            mock_factory.assert_called_once_with(id=1234,title="Rhubarb")
            mock_model.save.assert_not_called()
            mock_model.delete.assert_not_called()
