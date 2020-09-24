import lxml.etree as ET
from xml.sax.saxutils import unescape
import re

pair_splitter = re.compile(r'^(\w{2}-\d+)=(.*)$')


class JobNotification(object):
    """
    This class abstracts the Vidispine job notification document to allow for easier reading
    """

    def __init__(self, jsondict: dict):
        self._content = jsondict

    def __getattr__(self, item):
        for entry in self._content["field"]:
            if entry["key"]==item:
                return entry["value"]
        return None

    def __str__(self):
        return "{type} job for {filename} by {user}".format(type=self.type,filename=self.originalFilename,user=self.username)

    def file_paths(self):
        """
        returns a dictionary of relative file path/file ID pairs, from the filePathMap parameter
        :return: dictionary
        """
        if self.filePathMap is None:
            return None

        pairs = self.filePathMap.split(',')

        def split_pair(pair): #can't be sure that there will be no = in the filename
            result = pair_splitter.match(pair)
            if result:
                return (result.group(1), result.group(2))
            else:
                return None

        return dict([result for result in [split_pair(pair) for pair in pairs] if result is not None])
