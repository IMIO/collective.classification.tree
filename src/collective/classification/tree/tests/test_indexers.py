# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.indexers import classification_categories_index
from collective.classification.tree.utils import create_category
from imio.helpers import EMPTY_STRING
from plone import api

import unittest


class TestIndexers(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.portal
        )
        self.uid = create_category(
            container, {"identifier": "001", "title": "First"}
        ).UID()

    def test_classification_categories_index(self):
        classified = api.content.create(
            title="Classified",
            type="ClassifiedItem",
            container=self.portal,
            classification_categories=[self.uid],
        )
        unclassified = api.content.create(
            title="Unclassified", type="ClassifiedItem", container=self.portal
        )
        self.assertEqual([self.uid], classification_categories_index(classified)())
        self.assertEqual(
            [EMPTY_STRING], classification_categories_index(unclassified)()
        )
        # catalog index and metadata
        brains = api.content.find(classification_categories=self.uid)
        self.assertEqual([classified.UID()], [b.UID for b in brains])
        self.assertEqual([self.uid], brains[0].classification_categories)
        self.assertEqual(
            [unclassified.UID()],
            [b.UID for b in api.content.find(classification_categories=EMPTY_STRING)],
        )
