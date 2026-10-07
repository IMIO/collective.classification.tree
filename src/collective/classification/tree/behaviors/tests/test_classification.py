# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.behaviors.classification import IClassificationCategory
from collective.classification.tree.behaviors.classification import IClassificationCategoryMarker
from collective.classification.tree.utils import create_category
from collective.classification.tree.vocabularies import ClassificationTreeSource
from plone import api
from plone.autoform.interfaces import IFormFieldProvider

import unittest


class TestClassificationCategory(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        container = api.content.create(title="Container", type="ClassificationContainer", container=self.portal)
        self.enabled = create_category(container, {"identifier": u"001", "title": u"Enabled"}).UID()
        self.disabled = create_category(container, {"identifier": u"002", "title": u"Disabled", "enabled": False}).UID()
        self.item = api.content.create(title="Mail", type="ClassifiedItem", container=self.portal)

    def test_classification_categories(self):
        # the field: a list of enabled categories, from the tree source
        self.assertTrue(IFormFieldProvider.providedBy(IClassificationCategory))
        self.assertTrue(IClassificationCategoryMarker.providedBy(self.item))
        field = IClassificationCategory["classification_categories"].bind(self.item)
        source = field.value_type.vocabulary
        self.assertIsInstance(source, ClassificationTreeSource)
        self.assertEqual([u"001 - Enabled"], [t.title for t in source.search(u"abled")])
        # the adapter reads and writes the attribute of the content
        adapter = IClassificationCategory(self.item)
        self.assertIsNone(adapter.classification_categories)
        adapter.classification_categories = [self.enabled]
        self.assertEqual([self.enabled], self.item.classification_categories)
        self.assertEqual([self.enabled], adapter.classification_categories)
