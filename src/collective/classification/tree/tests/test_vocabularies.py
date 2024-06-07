# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.vocabularies import ClassificationTreeSource
from plone import api
from zope.component import createObject
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestCategoriesContents(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(id="folder", type="Folder", container=self.portal)
        self.container = api.content.create(title="Container", type="ClassificationContainer", container=self.folder)

    def tearDown(self):
        api.content.delete(self.folder)

    def _create_category(self, id, title, enabled=True):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        category.enabled = enabled
        return category

    def test_simple_vocabulary(self):
        """Test vocabulary values when there is only one category level"""
        for id, title in ((u"001", u"First"), (u"002", u"Second"), (u"003", u"Third")):
            category = self._create_category(id, title)
            self.container._add_element(category)

        vocabulary = getUtility(IVocabularyFactory, "collective.classification.vocabularies:tree")(self.folder)
        self.assertEqual(
            [u"001 - First", u"002 - Second", u"003 - Third"],
            [e.title for e in vocabulary],
        )

    def test_vocabulary_missing_title(self):
        """Test vocabulary values when title and identifier are the same"""
        for id, title in ((u"001", u"001"), (u"002", u"002"), (u"003", u"003")):
            category = self._create_category(id, title)
            self.container._add_element(category)

        vocabulary = getUtility(IVocabularyFactory, "collective.classification.vocabularies:tree")(self.folder)
        self.assertEqual(
            [u"001", u"002", u"003"],
            [e.title for e in vocabulary],
        )

    def test_multilevel_vocabulary(self):
        """Test vocabulary values when there is multiple category levels"""
        structure = (
            (u"001", u"First", ((u"001.1", u"first"), (u"001.2", u"second"))),
            (u"002", u"Second", ((u"002.1", u"first"),)),
        )
        for id, title, subelements in structure:
            category = self._create_category(id, title)
            self.container._add_element(category)
            if subelements:
                for id, title in subelements:
                    subcategory = self._create_category(id, title)
                    category._add_element(subcategory)
        last_element = category
        category = self._create_category(u"002.1.1", u"first")
        last_element._add_element(category)

        vocabulary = getUtility(IVocabularyFactory, "collective.classification.vocabularies:tree")(self.folder)
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

    def test_ClassificationtreeSource(self):
        for cid, title, enabled in (
            (u"001", u"Tâche", False),
            (u"002", u"Tache import dossier", True),
            (u"003", u"tâche", True),
            (u"004", u"tache", True),
            (u"005", u"Other", True),
        ):
            category = self._create_category(cid, title, enabled)
            self.container._add_element(category)
        cts = ClassificationTreeSource(self.container)
        terms = cts.vocabulary._terms
        self.assertFalse(terms[0].attrs["enabled"])
        self.assertTrue(terms[1].attrs["enabled"])
        self.assertEqual(len([t.title for t in cts.search(u"Othe")]), 1)
        self.assertEqual(len([t.title for t in cts.search(u"Unfound")]), 0)
        for term in (u"Tâche", u"Tache", u"tâche", u"tache"):
            res = [t.title for t in cts.search(term)]
            self.assertEqual(len(res), 4, term)
        self.assertEqual(len([t.title for t in cts.search(u"tache doss")]), 1)
        # find only disabled
        cts = ClassificationTreeSource(self.container, False)
        res = [t.title for t in cts.search(u"Tâche")]
        self.assertEqual(len(res), 1, term)
        # find only enabled
        cts = ClassificationTreeSource(self.container, True)
        res = [t.title for t in cts.search(u"Tâche")]
        self.assertEqual(len(res), 3, term)
