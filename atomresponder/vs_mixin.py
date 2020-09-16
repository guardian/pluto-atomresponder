from gnmvidispine.vs_collection import VSCollection
from gnmvidispine.vs_search import VSItemSearch
from gnmvidispine.vs_item import VSItem, VSNotFound
from django.conf import settings
import logging
from . import constants as const
from atomresponder.exceptions import NotAProjectError
from gnmvidispine.vs_item import VSItem
import datetime
logger = logging.getLogger(__name__)


class VSMixin(object):
    """
    Mixin class that abstracts vidispine operations

    """
    def get_item_for_atomid(self, atomid):
        """
        Returns a populated VSItem object for the master, or None if no such item exists
        :param atomid:
        :return:
        """
        try:
            item = VSItem(url=settings.VIDISPINE_URL, user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)
            item.populate(atomid)   # this will work if the item has an external id set to the atom id.
                                    #this is done in `create_placeholder_for_atomid`
            return item
        except VSNotFound:
            s = VSItemSearch(url=settings.VIDISPINE_URL,user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)
            s.addCriterion({const.GNM_DELIVERABLE_ATOM_ID: atomid, const.GNM_ASSET_CATEGORY: 'Deliverable'})
            result = s.execute()
            if result.totalItems==0:
                return None
            elif result.totalItems==1:
                return next(result.results(shouldPopulate=True))
            else:
                resultList = [item for item in result.results(shouldPopulate=False)]
                potential_master_ids = [item.name for item in resultList]
                logger.warning("Multiple masters returned for atom ID {0}: {1}. Using the first.".format(atomid, potential_master_ids))
                resultList[0].populate(resultList[0].name)
                return resultList[0]

    @staticmethod
    def create_placeholder_for_atomid(atomid, filename, project_id, title="unknown video", user="unknown_user"):
        """
        Creates a placeholder and returns a VSItem object for it
        :param atomid: atom ID string
        :param filename: path of the file to import
        :param project_id: ID number of the project that the video is associated with
        :param title: title of the new video
        :return: VSItem object
        """
        item = VSItem(url=settings.VIDISPINE_URL,user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)

        basemeta = {
            const.GNM_ASSET_CATEGORY: "Deliverable",
            const.GNM_ASSET_ORIGINAL_FILENAME: filename,
            const.GNM_ASSET_CONTAINING_PROJECTS: [project_id],
            const.GNM_ASSET_OWNER: user,
            const.GNM_ASSET_FILE_CREATED: datetime.datetime.now().isoformat("T")
        }

        builder = item.get_metadata_builder()
        builder.addMeta({'title': title})
        builder.addGroup(const.GROUP_GNM_ASSET, basemeta)
        # this needs to get filled in by deliverables
        # builder.addGroup(const.GROUP_GNM_DELIVERABLE, {
        #     const.GNM_DELIVERABLE_ATOM_ID: atomid
        # })

        mdbytes:bytes = builder.as_xml("UTF-8")
        item.createPlaceholder(mdbytes.decode("UTF-8"))
        item.add_external_id(atomid)
        return item

    def get_collection_for_id(self, projectid, expected_type="Project"):
        """
        Returns a VSCollection for the given project ID. Raises VSNotFound if the collection does not exist, or
        exceptions.NotAProject if it is not a project.
        :return:
        """
        collection = VSCollection(url=settings.VIDISPINE_URL,user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)
        collection.populate(projectid)
        if collection.get('gnm_type')!=expected_type:
            raise NotAProjectError("{0} is a {1}".format(projectid, collection.get('gnm_type')))
        return collection