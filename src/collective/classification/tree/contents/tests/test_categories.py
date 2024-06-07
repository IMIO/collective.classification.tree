# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from zope.component import createObject
from plone.app.content.interfaces import INameFromTitle
from plone import api

import unittest


class TestCategoriesContents(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(id="folder", type="Folder", container=self.portal)

    def tearDown(self):
        api.content.delete(self.folder)

    def test_container(self):
        container = api.content.create(title="Container", type="ClassificationContainer", container=self.folder)
        self.assertEqual("Container", container.Title())
        self.assertEqual("Container", INameFromTitle(container).title)
        self.assertEqual("container", container.id)

    def test_basic(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        self.assertEqual(0, len(container._tree))
        self.assertEqual(0, len(container))

        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)

        self.assertEqual(1, len(container._tree))
        self.assertEqual(1, len(container))
        self.assertTrue(category.UID() in container)
        self.assertTrue(bool(category))

    def test_multiple_category_levels(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category_lvl1 = createObject("ClassificationCategory")
        category_lvl1.identifier = u"001"
        category_lvl1.title = u"First"
        container._add_element(category_lvl1)

        category_lvl2 = createObject("ClassificationCategory")
        category_lvl2.identifier = u"001.1"
        category_lvl2.title = u"First"
        category_lvl1._add_element(category_lvl2)
        self.assertEqual(1, len(container))
        self.assertEqual(1, len(category_lvl1))

        category_lvl3 = createObject("ClassificationCategory")
        category_lvl3.identifier = u"001.1.1"
        category_lvl3.title = u"First"
        category_lvl2._add_element(category_lvl3)
        self.assertEqual(1, len(container))
        self.assertEqual(1, len(category_lvl1))
        self.assertEqual(1, len(category_lvl2))

    def test_update_category(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)

        element = container[category.UID()]
        self.assertEqual(u"First", element.title)

        category.title = u"Updated First"
        container._update_element(category)

        element = container[category.UID()]
        self.assertEqual(u"Updated First", element.title)

    def test_delete_category(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)

        self.assertEqual(1, len(container))
        container._delete_element(category)
        self.assertEqual(0, len(container))

    def test_iter_over_categories(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        uids = []
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)
        uids.append(category.UID())

        category = createObject("ClassificationCategory")
        category.identifier = u"002"
        category.title = u"Second"
        container._add_element(category)
        uids.append(category.UID())

        category = createObject("ClassificationCategory")
        category.identifier = u"003"
        category.title = u"Third"
        container._add_element(category)
        uids.append(category.UID())

        self.assertEqual(3, len(container))
        self.assertListEqual(
            sorted([u"001", u"002", u"003"]),
            sorted([e.identifier for e in container.values()]),
        )
        self.assertListEqual(sorted(uids), sorted([e for e in container]))
        self.assertListEqual(sorted(uids), sorted([e for e in container.keys()]))

    def test_traversing(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category_lvl1 = createObject("ClassificationCategory")
        category_lvl1.identifier = u"001"
        category_lvl1.title = u"First"
        container._add_element(category_lvl1)

        category_lvl2 = createObject("ClassificationCategory")
        category_lvl2.identifier = u"001.1"
        category_lvl2.title = u"First"
        category_lvl1._add_element(category_lvl2)

        path = "folder/container/{0}".format(category_lvl1.UID())
        element = self.portal.restrictedTraverse(path)
        self.assertEqual(u"001", element.identifier)

        path += "/{0}".format(category_lvl2.UID())
        element = self.portal.restrictedTraverse(path)
        self.assertEqual(u"001.1", element.identifier)
