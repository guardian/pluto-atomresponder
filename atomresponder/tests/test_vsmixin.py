import django.test
from mock import MagicMock, patch
from gnmvidispine.vs_item import VSItem
from gnmvidispine.vs_collection import VSCollection
from gnmvidispine.vs_search import VSItemSearch
import lxml.etree as ET
import atomresponder.constants as const


class TestVsMixin(django.test.TestCase):
    class MockSearchResult(object):
        def __init__(self, results):
            self._results = results
            self.totalItems = len(results)

        def results(self,shouldPopulate=False):
            for item in self._results:
                yield item

    class MockSearchClass(object):
        def execute(self):
            pass

    def test_get_item_for_atomid(self):
        """
        get_item_for_atomid should look up  atom id as an external ID
        :return:
        """
        from atomresponder.master_importer import MasterImportResponder

        mock_item = MagicMock(target=VSItem)

        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSItem', return_value = mock_item):

                r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")
                mock_refresh_creds.assert_called_once()

                result = r.get_item_for_atomid("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2")
                mock_item.populate.assert_called_once_with("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2")

                self.assertEqual(result, mock_item)

    def test_get_item_for_atomid_idnotfound(self):
        """
        get_item_for_atomid should make a search for the provided atom id if it is not found as an external ID
        :return:
        """
        from atomresponder.master_importer import MasterImportResponder
        from gnmvidispine.vidispine_api import VSNotFound
        from mock import call

        mock_item = MagicMock(target=VSItem)
        mock_item.populate = MagicMock(side_effect=[VSNotFound,None])
        mock_search = MagicMock(target=VSItemSearch)
        mock_search.addCriterion = MagicMock()
        mock_search.execute = MagicMock(return_value=self.MockSearchResult([mock_item]))
        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSItemSearch', return_value = mock_search):
                with patch('atomresponder.vs_mixin.VSItem', return_value = mock_item):
                    r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")
                    mock_refresh_creds.assert_called_once()

                    result = r.get_item_for_atomid("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2")
                    mock_search.addCriterion.assert_called_once_with(
                        {const.GNM_DELIVERABLE_ATOM_ID: "f6ba9036-3f53-4850-9c75-fe3bcfbae4b2",
                         const.GNM_ASSET_CATEGORY: 'Deliverable'}
                    )

                    mock_item.populate.assert_has_calls([
                        call("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2"),
                    ])
                self.assertEqual(result, mock_item)

    def test_get_item_for_atomid_notfound(self):
        """
        get_item_for_atomid should return None if no item exists
        :return:
        """
        from atomresponder.master_importer import MasterImportResponder
        from gnmvidispine.vidispine_api import VSNotFound

        mock_item = MagicMock(target=VSItem)
        mock_item.populate = MagicMock(side_effect=VSNotFound)

        mock_search = MagicMock(target=VSItemSearch)
        mock_search.addCriterion = MagicMock()
        mock_search.execute = MagicMock(return_value=self.MockSearchResult([]))
        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSItemSearch', return_value = mock_search):
                with patch('atomresponder.vs_mixin.VSItem', return_value = mock_item):
                    r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")
                    mock_refresh_creds.assert_called_once()

                    result = r.get_item_for_atomid("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2")
                    mock_search.addCriterion.assert_called_once_with(
                        {const.GNM_DELIVERABLE_ATOM_ID: "f6ba9036-3f53-4850-9c75-fe3bcfbae4b2",
                         const.GNM_ASSET_CATEGORY: 'Deliverable'}
                    )

                self.assertEqual(result, None)

    def test_get_item_for_atomid_multiple(self):
        """
        get_item_for_atomid should return the first item if multiple records match
        :return:
        """
        from atomresponder.master_importer import MasterImportResponder
        from gnmvidispine.vidispine_api import VSNotFound

        mock_item = MagicMock(target=VSItem)
        #populate is also called when we have found the item via vs search - hence second one succeeds
        #test is only relevant if the initial lookup fails, as VS ensures that external IDs are unique
        mock_item.populate = MagicMock(side_effect=[VSNotFound,None])
        mock_search = MagicMock(target=VSItemSearch)
        mock_search.addCriterion = MagicMock()
        mock_search.execute = MagicMock(return_value=self.MockSearchResult([mock_item, MagicMock(target=VSItem), MagicMock(target=VSItem)]))
        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSItemSearch', return_value = mock_search):
                with patch('atomresponder.vs_mixin.VSItem', return_value = mock_item):
                    r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")
                    mock_refresh_creds.assert_called_once()

                    result = r.get_item_for_atomid("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2")
                    mock_search.addCriterion.assert_called_once_with(
                        {const.GNM_DELIVERABLE_ATOM_ID: "f6ba9036-3f53-4850-9c75-fe3bcfbae4b2",
                         const.GNM_ASSET_CATEGORY: 'Deliverable'}
                    )

                    self.assertEqual(result, mock_item)

    @staticmethod
    def assertXmlContainsValue(xmlContent, key, value):
        ns = {"vs": "http://xml.vidispine.com/schema/vidispine"}
        field_nodes = xmlContent.xpath('//vs:name[text()="{}"]'.format(key), namespaces=ns)

        if len(field_nodes)==0:
            raise AssertionError("field {} does not exist".format(key))

        for field_node in field_nodes:
            matching_value_nodes = field_node.getparent().xpath('//vs:value[text()="{}"]'.format(value), namespaces=ns)
            if len(matching_value_nodes)>0:
                return
        print(ET.tostring(xmlContent))
        raise AssertionError("field {} does exist but without wanted value".format(key))

    def test_create_placeholder_for_atomid(self):
        """
        create_placeholder_for_atomid should create a placeholder with relevant metadata
        :return:
        """
        from gnmvidispine.vs_metadata import VSMetadataAttribute,VSMetadataReference, VSMetadataValue
        from gnmvidispine.vs_item import VSMetadataBuilder
        from atomresponder.master_importer import MasterImportResponder

        mock_item = MagicMock(target=VSItem)
        mock_item.host="localhost"
        mock_item.port=8080
        mock_item.createPlaceholder = MagicMock()
        builder = VSMetadataBuilder(mock_item)
        mock_item.get_metadata_builder = MagicMock(return_value=builder)

        mock_project = MagicMock(target=VSCollection)
        mock_project_name_attrib = MagicMock(target=VSMetadataAttribute)
        mock_project_name_attrib.uuid = "c4a7cd79-7652-47ba-bd3b-37492cdb91aa"
        mock_project_name_attrib.values = [VSMetadataValue(uuid="B9A8D873-F704-4BA0-A339-17BF456FEA7C")]
        mock_commission_name_attrib = MagicMock(target=VSMetadataAttribute)
        mock_commission_name_attrib.references = [VSMetadataReference(uuid="8CDFBE79-7F08-4D66-9048-0CC33F664937")]
        mock_commission_name_attrib.uuid = "41cce471-2b30-48fa-8af2-b0d42aff6c7f"

        mock_project.get_metadata_attributes = MagicMock(side_effect=[
            [mock_project_name_attrib],
            [mock_commission_name_attrib]
        ])

        self.assertEqual(VSMetadataReference(uuid="B9A8D873-F704-4BA0-A339-17BF456FEA7C"),VSMetadataReference(uuid="B9A8D873-F704-4BA0-A339-17BF456FEA7C"))
        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSItem', return_value=mock_item):
                r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")
                mock_refresh_creds.assert_called_once()
                r.create_placeholder_for_atomid("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2",
                                                "/path/to/downloaded/file",
                                                "2345",
                                                title="fake title",
                                                user="joe.bloggs@mydomain.com")

                parsed_content = ET.fromstring(builder.as_xml("UTF-8"))
                self.assertXmlContainsValue(parsed_content, "title","fake title")
                self.assertXmlContainsValue(parsed_content, const.GNM_ASSET_CATEGORY, "Deliverable")
                self.assertXmlContainsValue(parsed_content, const.GNM_ASSET_ORIGINAL_FILENAME, "/path/to/downloaded/file")
                self.assertXmlContainsValue(parsed_content, const.GNM_ASSET_CONTAINING_PROJECTS,"2345")
                self.assertXmlContainsValue(parsed_content, const.GNM_ASSET_OWNER, "joe.bloggs@mydomain.com")

                mock_item.createPlaceholder.assert_called_once_with(builder.as_xml("UTF-8").decode("UTF-8"))
                mock_item.add_external_id.assert_called_once_with("f6ba9036-3f53-4850-9c75-fe3bcfbae4b2")

    def test_get_collection_for_projectid(self):
        from atomresponder.master_importer import MasterImportResponder

        mock_collection = MagicMock(target=VSCollection)
        mock_collection.populate = MagicMock()
        mock_collection.get = MagicMock(return_value='Project')

        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSCollection', return_value=mock_collection):
                r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")

                result = r.get_collection_for_id("VX-234")
                mock_collection.populate.assert_called_once_with("VX-234")
                self.assertEqual(result, mock_collection)

    def test_get_collection_for_projectid_invalid(self):
        """
        get_collection_for_projectid should raise an exception if the returned collection is not a project
        :return:
        """
        from atomresponder.master_importer import MasterImportResponder
        from atomresponder.exceptions import NotAProjectError

        mock_collection = MagicMock(target=VSCollection)
        mock_collection.populate = MagicMock()
        mock_collection.get = MagicMock(return_value='Gumby')

        with patch('atomresponder.master_importer.MasterImportResponder.refresh_access_credentials') as mock_refresh_creds:
            with patch('atomresponder.vs_mixin.VSCollection', return_value=mock_collection):
                r = MasterImportResponder("fake role", "fake session", "fake stream", "shard-00000")

                with self.assertRaises(NotAProjectError) as excep:
                    result = r.get_collection_for_id("VX-234")
                mock_collection.populate.assert_called_once_with("VX-234")
                self.assertEqual(str(excep.exception),"VX-234 is a Gumby")
