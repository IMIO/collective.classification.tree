# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import unittest


class TestSerializeToJson(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        container = api.content.create(title="Container", type="ClassificationContainer", container=self.portal)
        data = {"identifier": u"001", "title": u"First", "informations": u"Info", "enabled": False}
        self.category = container[create_category(container, data).UID()]
        self.serializer = getMultiAdapter((self.category, self.request), ISerializeToJson)

    def test___call__(self):
        url = self.category.absolute_url()
        self.assertEqual(
            {
                "@id": url,
                "UID": self.category.UID(),
                "identifier": u"001",
                "title": u"First",
                "informations": u"Info",
                "enabled": u"No",
                "links": [
                    {"title": u"Edit", "link": url + "/edit"},
                    {"title": u"Add", "link": url + "/add-ClassificationCategory"},
                ],
            },
            self.serializer(),
        )
        self.category.enabled = True
        self.assertEqual(u"Yes", self.serializer()["enabled"])

    @testing.plone6_bug
    def test__links(self):
        self.assertEqual(2, len(self.serializer._links))
        # plone.api 2 raises InvalidParameterError for "cmf.ModifyPortalContent" (not a permission title)
        # when the user doesn't have it on the portal
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        self.assertEqual([], self.serializer._links)
