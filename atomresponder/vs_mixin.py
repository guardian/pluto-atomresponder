from gnmvidispine.vs_collection import VSCollection
from gnmvidispine.vs_search import VSItemSearch
from gnmvidispine.vs_item import VSItem, VSNotFound
from django.conf import settings
import logging
from . import constants as const
from atomresponder.exceptions import NotAProjectError
from gnmvidispine.vs_item import VSItem
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
            item.populate(atomid)   #this will work if the item has an external id set to the atom id. this is done in `set_project_fields_for_master`
            return item
        except VSNotFound:
            s = VSItemSearch(url=settings.VIDISPINE_URL,user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)
            s.addCriterion({const.GNM_MASTERS_MEDIAATOM_ATOMID: atomid, const.GNM_TYPE: 'Master'})
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
    def get_userid_for_email(email_address):
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=email_address)
            logger.info("Got user {0} with id {1} for email {2}".format(user.username, user.pk, email_address))
            return user.pk
        except User.DoesNotExist:
            logger.info("Could not find any user for email {0}".format(email_address))
            return None

    @staticmethod
    def create_placeholder_for_atomid(atomid, title="unknown video", user="unknown_user", parent=None):
        """
        Creates a placeholder and returns a VSItem object for it
        :param atomid: atom ID string
        :param title: title of the new video
        :return: VSItem object
        """
        from gnmvidispine.vs_metadata import VSMetadataReference
        item = VSItem(url=settings.VIDISPINE_URL,user=settings.VIDISPINE_USERNAME,passwd=settings.VIDISPINE_PASSWORD)

        project_name_attribs = parent.get_metadata_attributes(const.GNM_PROJECT_HEADLINE)

        project_name_reference = VSMetadataReference(uuid=project_name_attribs[0].uuid)

        commission_name_attribs = parent.get_metadata_attributes(const.GNM_COMMISSION_TITLE)
        commission_name_ref = VSMetadataReference(uuid=commission_name_attribs[0].uuid)

        metadata = {const.GNM_TYPE: 'Master',
                    'title': title,
                    const.GNM_MASTERS_WEBSITE_HEADLINE: title,
                    const.GNM_MASTERS_MEDIAATOM_ATOMID: atomid,
                    const.GNM_MASTERS_GENERIC_TITLEID: atomid,
                    const.GNM_ASSET_CATEGORY: "Master",
                    const.GNM_MASTERS_MEDIAATOM_UPLOADEDBY: user,
                    const.GNM_PROJECT_HEADLINE: project_name_reference,
                    const.GNM_COMMISSION_TITLE: commission_name_ref
                    }
        userid = VSMixin.get_userid_for_email(user)
        if userid is not None:
            metadata.update({
                const.GNM_MASTERS_GENERIC_OWNER: userid
            })

        item.createPlaceholder(metadata, group='Asset')
        item.add_external_id(atomid)
        return item

    @staticmethod
    def set_project_fields_for_master(vsitem, parent_project):
        """
        Sets the metadata reference fields on the given master. Raises VSExceptions if the operations fail.
        :param vsitem: populated VSItem of the master to update
        :param parent_project: populated VSCollection of the project it is being added to
        :return: the item passed in
        """
        from gnmvidispine.vs_metadata import VSMetadataReference
        project_name_attribs = parent_project.get_metadata_attributes(const.GNM_PROJECT_HEADLINE)
        project_name_reference = VSMetadataReference(uuid=project_name_attribs[0].uuid)

        commission_name_attribs = parent_project.get_metadata_attributes(const.GNM_COMMISSION_TITLE)
        commission_name_ref = VSMetadataReference(uuid=commission_name_attribs[0].uuid)

        metadata = {
            const.GNM_PROJECT_HEADLINE: project_name_reference,
            const.GNM_COMMISSION_TITLE: commission_name_ref
        }
        vsitem.set_metadata(metadata, group="Asset")
        return vsitem

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