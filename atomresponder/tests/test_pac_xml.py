## Commented out as this functionality will probably be removed, but kept for reference during development
# import django.test
# from mock import MagicMock, patch
# from django.core.management import execute_from_command_line
# import os.path
#
# class TestPacXmlProcessor(django.test.TestCase):
#     fixtures = [
#         "PacFormXml.yaml",
#         "Users.yaml"
#     ]
#
#     def test_link_to_item(self):
#         from atomresponder.pac_xml import PacXmlProcessor
#         from atomresponder.models import PacFormXml
#         from django.contrib.auth.models import User
#         from gnmvidispine.vs_item import VSItem
#
#         pacdata = PacFormXml.objects.get(atom_id='57AF5F3B-A556-448B-98E1-0628FDE9A5AC')
#         master_item = MagicMock(target=VSItem)
#         user = User.objects.get(username='admin')
#
#         with patch('__builtin__.open', create=True) as mock_open:
#             mock_open.return_value = MagicMock(spec=file)
#             p = PacXmlProcessor("fake_role","fake_session")
#
#             p.download_to_local_location = MagicMock(return_value="/path/to/local/datafile")
#
#             p.link_to_item(pacdata, master_item)
#
#             p.download_to_local_location.assert_called_once_with(bucket="bucketname",key="path/to/content.xml")
#             file_handle = mock_open.return_value.__enter__.return_value
#             edl_import_mock.update_edl_data.assert_called_once_with(file_handle, master_item.name, user)