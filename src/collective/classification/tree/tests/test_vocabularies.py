# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from plone import api
from zope.component import createObject
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestCategoriesContents(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(
            id="folder", type="Folder", container=self.portal
        )

    def tearDown(self):
        api.content.delete(self.folder)

    def _create_category(self, id, title):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        return category

    def test_simple_vocabulary(self):
        """Test vocabulary values when there is only one category level"""
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.folder
        )
        for id, title in ((u"001", u"First"), (u"002", u"Second"), (u"003", u"Third")):
            category = self._create_category(id, title)
            container._add_element(category)

        vocabulary = getUtility(
            IVocabularyFactory, "collective.classification.vocabularies:tree"
        )(self.folder)
        self.assertEqual(
            [u"001 - First", u"002 - Second", u"003 - Third"],
            [e.title for e in vocabulary],
        )

    def test_multilevel_vocabulary(self):
        """Test vocabulary values when there is multiple category levels"""
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.folder
        )
        structure = (
            (u"001", u"First", ((u"001.1", u"first"), (u"001.2", u"second"))),
            (u"002", u"Second", ((u"002.1", u"first"),)),
        )
        for id, title, subelements in structure:
            category = self._create_category(id, title)
            container._add_element(category)
            if subelements:
                for id, title in subelements:
                    subcategory = self._create_category(id, title)
                    category._add_element(subcategory)
        last_element = category
        category = self._create_category(u"002.1.1", u"first")
        last_element._add_element(category)

        vocabulary = getUtility(
            IVocabularyFactory, "collective.classification.vocabularies:tree"
        )(self.folder)
        self.assertEqual(
            [
                u"001 - First",
                u"001.1 - first",
                u"001.2 - second",
                u"002 - Second",
                u"002.1 - first",
                u"002.1.1 - first",
            ],
            [e.title for e in vocabulary],
        )