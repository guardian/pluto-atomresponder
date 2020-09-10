# import django.test
# from mock import MagicMock, patch, call
# from django.core.management import execute_from_command_line
#
#
# class TestTasks(django.test.TestCase):
#     fixtures = [
#         'ImportJobs.yaml',
#         'PacFormXml.yaml'
#     ]
#
#     def test_cleanup_old_importjobs(self):
#         """
#         cleanup_old_importjobs should purge out jobs older than 60 days
#         :return:
#         """
#         from atomresponder.models import ImportJob
#         from atomresponder.tasks import cleanup_old_importjobs
#         #FIXME: should patch datetime.now() to always return the same value, for time being rely on fixture values being much
#         #older than 60 days.
#         self.assertEqual(ImportJob.objects.all().count(), 6)
#         cleanup_old_importjobs()
#         self.assertEqual(ImportJob.objects.all().count(), 4)
#
#     def test_delete_from_s3(self):
#         """
#         delete_from_s3 should, well, delete from s3
#         :return:
#         """
#         from atomresponder.models import ImportJob
#         from atomresponder.tasks import delete_from_s3
#         from django.conf import settings
#         from datetime import datetime
#         from boto.s3.bucket import Bucket
#
#         mock_bucket = MagicMock(target=Bucket)
#         mock_connection = MagicMock()
#         mock_connection.get_bucket = MagicMock(return_value=mock_bucket)
#
#         testjob = ImportJob(item_id="VX-123",job_id="VX-456", status="FINISHED",started_at=datetime.now(), s3_path="/path/to/s3/file")
#         testjob.save = MagicMock()
#
#         delete_from_s3(mock_connection, testjob)
#         mock_connection.get_bucket.assert_called_once_with(settings.ATOM_RESPONDER_DOWNLOAD_BUCKET)
#         mock_bucket.delete_key.assert_called_once_with("/path/to/s3/file")
#         testjob.save.assert_called_once()
#
#     def test_check_unprocessed_pacxml(self):
#         """
#         check_unprocessed_pacxml should pick up items that have not been processed and process them if possible
#         :return:
#         """
#         from atomresponder.tasks import check_unprocessed_pacxml
#         from atomresponder.pac_xml import PacXmlProcessor
#         from atomresponder.models import PacFormXml
#         from atomresponder.vs_mixin import VSMixin
#         from gnmvidispine.vs_item import VSItem
#
#         mock_processor = MagicMock(target=PacXmlProcessor)
#         mock_processor.link_to_item = MagicMock()
#
#         mock_item = MagicMock(target=VSItem)
#         mock_item.name = "VX-123"
#
#         mock_vs = MagicMock(target=VSMixin)
#         mock_vs.get_item_for_atomid = MagicMock(side_effect=[mock_item, None])
#
#         expected_record = PacFormXml.objects.get(atom_id="57AF5F3B-A556-448B-98E1-0628FDE9A5AC")
#
#         with patch("atomresponder.pac_xml.PacXmlProcessor", return_value=mock_processor):
#             with patch("atomresponder.vs_mixin.VSMixin", return_value=mock_vs):
#                 check_unprocessed_pacxml()
#                 #these are the only two "unprocessed" entries in the fixture data
#                 mock_vs.get_item_for_atomid.assert_has_calls([call("57AF5F3B-A556-448B-98E1-0628FDE9A5AC"),
#                                                               call("765EE342-0368-4A49-AB73-D1C887BD8D28")])
#                 #and only one of them has returned an item (from the get_item_for_atomid mock)
#                 mock_processor.link_to_item.assert_called_once_with(expected_record, mock_item)
#
#     def test_expire_processed_pacrecords(self):
#         """
#         expire_processed_pacrecords should delete records from the database and request deletion of the xml files from s3
#         :return:
#         """
#         from atomresponder.tasks import expire_processed_pacrecords
#         from atomresponder.models import PacFormXml
#
#         mock_conn = MagicMock()
#
#         self.assertEqual(1, PacFormXml.objects.filter(status="PROCESSED").count())
#
#         with patch("atomresponder.tasks.delete_s3_url") as mock_delete_s3_url:
#             with patch("atomresponder.s3_mixin.S3Mixin.get_s3_connection", return_value=mock_conn) as mock_get_s3_connection:
#                 expire_processed_pacrecords()
#                 mock_delete_s3_url.assert_called_once_with(mock_conn, "s3://bucketname/path/to/donecontent.xml")
#
#         self.assertEqual(0, PacFormXml.objects.filter(status="PROCESSED").count())
#
#     def test_delete_s3_url(self):
#         """
#         delete_s3_url should do what it says on the tin
#         :return:
#         """
#         from atomresponder.tasks import delete_s3_url
#
#         mock_bucket=MagicMock()
#         mock_bucket.delete_key=MagicMock(return_value=True)
#
#         conn = MagicMock()
#         conn.get_bucket = MagicMock(return_value=mock_bucket)
#
#         delete_s3_url(conn,"s3://bucketname/path/to/somefile")
#         conn.get_bucket.assert_called_once_with("bucketname")
#         mock_bucket.delete_key.assert_called_once_with("path/to/somefile")
#
#     def test_delete_s3_url_invalid(self):
#         """
#         delete_s3_url should raise a valueerror if the given url is not s3
#         :return:
#         """
#         from atomresponder.tasks import delete_s3_url
#
#         mock_bucket=MagicMock()
#         mock_bucket.delete_key=MagicMock(return_value=True)
#
#         conn = MagicMock()
#         conn.get_bucket = MagicMock(return_value=mock_bucket)
#
#         with self.assertRaises(ValueError):
#             delete_s3_url(conn,"https://bucketname/path/to/somefile")
#
#     def test_timed_request_resend(self):
#         """
#         timed_request_resend should call out to request_atom_resend
#         :return:
#         """
#         with patch("atomresponder.media_atom.request_atom_resend") as mock_resend:
#             from atomresponder.tasks import timed_request_resend
#
#             timed_request_resend('060386C2-3764-47F9-B338-F71E4E0704A7')
#             mock_resend.assert_called_once_with('060386C2-3764-47F9-B338-F71E4E0704A7','https://atomtool','sauce')