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
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.portal
        )
        data = {
            "identifier": "001",
            "title": "First",
            "informations": "Info",
            "enabled": False,
        }
        self.category = container[create_category(container, data).UID()]
        self.serializer = getMultiAdapter(
            (self.category, self.request), ISerializeToJson
        )

    def test___call__(self):
        url = self.category.absolute_url()
        self.assertEqual(
            {
                "@id": url,
                "UID": self.category.UID(),
                "identifier": "001",
                "title": "First",
                "informations": "Info",
                "enabled": "No",
                "links": [
                    {"title": "Edit", "link": url + "/edit"},
                    {"title": "Add", "link": url + "/add-ClassificationCategory"},
                ],
            },
            self.serializer(),
        )
        self.category.enabled = True
        self.assertEqual("Yes", self.serializer()["enabled"])

    def test__links(self):
        other = api.content.create(
            title="Other", type="ClassificationContainer", container=self.portal
        )
        other.manage_delLocalRoles([TEST_USER_ID])  # not Owner
        uid = create_category(other, {"identifier": "002", "title": "Second"}).UID()
        other_serializer = getMultiAdapter((other[uid], self.request), ISerializeToJson)
        self.assertEqual(2, len(self.serializer._links))
        setRoles(self.portal, TEST_USER_ID, ["Site Administrator"])
        self.assertEqual(2, len(self.serializer._links))
        # checked on the category, with the local roles of its container
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        self.assertEqual(2, len(self.serializer._links))  # Owner
        self.assertEqual([], other_serializer._links)
