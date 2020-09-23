# from mock import MagicMock, patch
# import django.test
# import os
# import json
# from django.core.management import execute_from_command_line
#
#
# class TestNotification(django.test.TestCase):
#     fixtures = [
#         'ImportJobs.yaml'
#     ]
#
#     @staticmethod
#     def _get_test_data(filename)->dict:
#         mypath = os.path.abspath(os.path.dirname(__file__))
#         with open(os.path.join(mypath, "data", filename)) as f:
#             return json.loads(f.read())
#
#     def test_process_notification(self):
#         """
#         process_notification should update the database with the status of the job that came back,
#         and should call handle_failed_job if there was an error
#         :return:
#         """
#         from rabbitmq.job_notification import JobNotification
#         from atomresponder.models import ImportJob
#         from gnmvidispine.vs_item import VSItem
#         mock_vsitem = MagicMock(target=VSItem)
#         mock_vsitem.transcode = MagicMock(return_value="VX-888")
#
#         with patch("gnmvidispine.vs_item.VSItem", return_value=mock_vsitem) as VSItemFactory:
#             with patch("atomresponder.notification.handle_failed_job") as mock_handle_failed_job:
#                 data = JobNotification(self._get_test_data("sample_notification.xml"))
#                 before_record = ImportJob.objects.get(job_id=data.jobId)
#                 self.assertEqual(before_record.status,'STARTED')
#                 process_notification(data)
#                 after_record = ImportJob.objects.get(job_id=data.jobId)
#                 self.assertEqual(after_record.status,'FINISHED_WARNING')
#                 mock_handle_failed_job.assert_called_once_with(before_record)
#
#     def test_process_notification_worked(self):
#         """
#         process_notification should update the database with the status of the job that came back,
#         and should NOT call handle_failed_job if there was no error
#         :return:
#         """
#         from rabbitmq.job_notification import JobNotification
#         from atomresponder.models import ImportJob
#         from gnmvidispine.vs_item import VSItem
#         mock_vsitem = MagicMock(target=VSItem)
#         mock_vsitem.transcode = MagicMock(return_value="VX-888")
#
#         with patch("gnmvidispine.vs_item.VSItem", return_value=mock_vsitem) as VSItemFactory:
#             with patch("atomresponder.notification.handle_failed_job") as mock_handle_failed_job:
#                 from atomresponder.notification import process_notification
#                 data = JobNotification(self._get_test_data("sample_notification_2.xml"))
#                 before_record = ImportJob.objects.get(job_id=data.jobId)
#                 self.assertEqual(before_record.status,'STARTED')
#                 process_notification(data)
#                 after_record = ImportJob.objects.get(job_id=data.jobId)
#                 self.assertEqual(after_record.status,'FINISHED')
#                 mock_handle_failed_job.assert_not_called()