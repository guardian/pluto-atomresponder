import requests
from django.core.management.base import BaseCommand
import hashlib
import copy
from email.utils import formatdate
import hmac
import logging
import time
import sys
from rabbitmq.models import CachedCommission
from rabbitmq.serializers import CachedCommissionSerializer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "directly re-synchronise our cache of commissions data with pluto-core"

    def add_arguments(self, parser):
        parser.add_argument("--server",type=str,help="URL location of the pluto-core instance to sync with")
        parser.add_argument("--secret", type=str, help="shared secret for auth with pluto-core")

    @staticmethod
    def sign_request(original_headers:dict, method:str, path:str, content_type:str, content_body:str, shared_secret:str) -> dict:
        """
        returns a dictionary including a suitable authorization header
        :param original_headers: original content headers
        :param content_body: data that is being sent
        :return: new headers dictionary
        """
        new_headers = copy.deepcopy(original_headers)

        content_hasher = hashlib.sha384()
        content_hasher.update(content_body.encode("UTF-8"))

        nowdate = formatdate(usegmt=True)
        checksumstring = content_hasher.hexdigest()
        new_headers['Digest'] = "SHA-384=" + checksumstring
        new_headers['Content-Length'] = str(len(content_body))
        new_headers['Content-Type'] = content_type
        new_headers['Date'] = nowdate

        string_to_sign = """{path}\n{date}\n{content_type}\n{checksum}\n{method}""".format(
            date=nowdate,content_type=content_type,checksum=checksumstring,
            method=method,path=path
        )

        print("debug: string to sign: {0}".format(string_to_sign))

        hmaccer = hmac.new(shared_secret.encode("UTF-8"), string_to_sign.encode("UTF-8"), hashlib.sha384)
        result = hmaccer.hexdigest()
        print("debug: final digest is {0}".format(result))
        new_headers['Authorization'] = "HMAC {0}".format(result)
        return new_headers

    def next_page_of_commissions(self, url:str, shared_secret:str, start_at:int, length:int):
        """
        generator that yields a commission dictionary
        :param url:
        :param shared_secret:
        :param start_at:
        :param length:
        :return:
        """
        urlpath = "/api/pluto/commission?startAt={}&length={}".format(start_at, length)
        signed_headers = Command.sign_request({}, "GET", urlpath, "application/octet-stream", "", shared_secret)

        response = requests.get(url + urlpath, headers=signed_headers, verify=False)
        if response.status_code==200:
            content = response.json()
            for entry in content["result"]:
                yield entry
        elif response.status_code==404:
            raise Exception("Endpoint not found? This indicates a code bug")
        elif response.status_code==503 or response.status_code==502:
            logger.warning("pluto-core not responding. Trying again in a few seconds...")
            time.sleep(3)
            for entry in self.next_page_of_commissions(url, shared_secret, start_at, length):
                yield entry
        else:
            logger.error("Server error {0}".format(response.status_code))
            logger.error(response.text)
            raise Exception("Server error")

    def process_entry(self, entry:dict):
        """
        handle a raw data structure from pluto-core
        :param entry:
        :return:
        """
        serializer = CachedCommissionSerializer(data=entry)
        if not serializer.is_valid():
            logger.warning("Data for {} was not valid".format(entry))
            return

        commission = CachedCommission(**serializer.validated_data)
        logger.debug("updating cachedcommission {}".format(commission.title))
        commission.save()

    def handle(self, *args, **options):
        if not options["server"] or not options["secret"]:
            logger.error("You must specify --server and --secret on the command line")
            sys.exit(1)

        page_size = 100
        start_at = 0

        while True:
            processed = 0
            for entry in self.next_page_of_commissions(options["server"], options["secret"], start_at, page_size):
                self.process_entry(entry)
                start_at += 1
                processed += 1
            if processed==0:
                logger.info("All done - processed {} commissions".format(start_at))
                break

