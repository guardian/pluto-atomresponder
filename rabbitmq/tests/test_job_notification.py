import unittest2
import os
import json


class TestJobNotification(unittest2.TestCase):
    @staticmethod
    def _get_test_data(filename):
        mypath = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(mypath, "data", filename)) as f:
            raw_content = f.read().encode('UTF-8')
            parsed_content = json.loads(raw_content)
            return parsed_content

    def test_read_data(self):
        """
        JobNotification should read the provided XML and allow simple access to key/value data
        :return:
        """
        from rabbitmq.job_notification import JobNotification
        j = JobNotification(self._get_test_data("samplemessage.json"))

        self.assertEqual(j.jobId,"VX-237")
        self.assertEqual(j.status,"FINISHED")
        self.assertEqual(j.transcoder, "http://10.235.51.119:8888/")
        self.assertEqual(j.invalidKey, None)

    def test_file_paths(self):
        """
        JobNotification should decode the filePathMap parameter to a dictionary of fileid->relative path pairs
        :return:
        """
        from rabbitmq.job_notification import JobNotification
        j = JobNotification(self._get_test_data("samplemessage.json"))

        self.assertDictEqual(j.file_paths(),{'VX-704': 'VX-704.mp4', 'VX-705': 'VX-705.mov'})