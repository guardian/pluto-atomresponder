from rest_framework.test import APITestCase, APIClient
from mock import MagicMock, patch


class TestResyncToAtomApiView(APITestCase):
    class MockResponse(object):
        def __init__(self, status_code, json_dict):
            self.status_code = status_code
            self.json_dict = json_dict

        def json(self):
            return self.json_dict

        def content(self):
            return str(self.json_dict)
#
#     def test_resync_normal(self):
#         """
#         a request should trigger a resync
#         :return:
#         """
#         client = APIClient()
#
#         mock_master = MagicMock()
#         mock_master.get = MagicMock(return_value="09239f72-e0a5-4299-ba5e-ec18c27117b4")
# #        with patch('__builtin__.__import__', side_effect=import_mock):
#         with patch('requests.put', return_value=self.MockResponse(200,{"some": "data","here":"now"})) as mock_put:
#             #with patch("portal.plugins.gnm_masters.models.VSMaster", return_value=mock_master):
#             models_mock.VSMaster = MagicMock(return_value=mock_master)
#             response = client.get(reverse_lazy("resync_to_atom", kwargs={"item_id":"VX-123"}))
#             self.assertEqual(response.status_code,200)
#             self.assertDictEqual(json.loads(response.content),{"some": "data","here":"now"})
#             mock_put.assert_called_once_with("https://launchdetector/update/09239f72-e0a5-4299-ba5e-ec18c27117b4")
#
