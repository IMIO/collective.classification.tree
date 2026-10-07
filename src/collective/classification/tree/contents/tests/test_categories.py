# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.contents.category import default_identifier
from collective.classification.tree.utils import create_category
from collective.classification.tree.utils import iterate_over_tree_data
from plone import api
from plone.app.content.interfaces import INameFromTitle
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect
from zope.component import createObject

import transaction
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

    def test_container(self):
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.folder
        )
        self.assertEqual("Container", container.Title())
        self.assertEqual("Container", INameFromTitle(container).title)
        self.assertEqual("container", container.id)

    def test_basic(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        self.assertEqual(0, len(container._tree))
        self.assertEqual(0, len(container))

        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)

        self.assertEqual(1, len(container._tree))
        self.assertEqual(1, len(container))
        self.assertTrue(category.UID() in container)
        self.assertTrue(bool(category))

    def test_default_identifier(self):
        """No RecursionError for a category without identifier"""
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        self.assertEqual("?", default_identifier(container))
        category = createObject("ClassificationCategory")
        self.assertEqual("?", default_identifier(category))
        self.assertEqual("?", category.identifier)
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)
        self.assertEqual("001?", default_identifier(container[category.UID()]))

    def test_multiple_category_levels(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category_lvl1 = createObject("ClassificationCategory")
        category_lvl1.identifier = "001"
        category_lvl1.title = "First"
        container._add_element(category_lvl1)

        category_lvl2 = createObject("ClassificationCategory")
        category_lvl2.identifier = "001.1"
        category_lvl2.title = "First"
        category_lvl1._add_element(category_lvl2)
        self.assertEqual(1, len(container))
        self.assertEqual(1, len(category_lvl1))

        category_lvl3 = createObject("ClassificationCategory")
        category_lvl3.identifier = "001.1.1"
        category_lvl3.title = "First"
        category_lvl2._add_element(category_lvl3)
        self.assertEqual(1, len(container))
        self.assertEqual(1, len(category_lvl1))
        self.assertEqual(1, len(category_lvl2))

    def test_update_category(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)

        element = container[category.UID()]
        self.assertEqual("First", element.title)

        category.title = "Updated First"
        container._update_element(category)

        element = container[category.UID()]
        self.assertEqual("Updated First", element.title)

    def test_delete_category(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)

        self.assertEqual(1, len(container))
        container._delete_element(category)
        self.assertEqual(0, len(container))

    def test_iter_over_categories(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        uids = []
        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)
        uids.append(category.UID())

        category = createObject("ClassificationCategory")
        category.identifier = "002"
        category.title = "Second"
        container._add_element(category)
        uids.append(category.UID())

        category = createObject("ClassificationCategory")
        category.identifier = "003"
        category.title = "Third"
        container._add_element(category)
        uids.append(category.UID())

        self.assertEqual(3, len(container))
        self.assertListEqual(
            sorted(["001", "002", "003"]),
            sorted([e.identifier for e in container.values()]),
        )
        self.assertListEqual(sorted(uids), sorted([e for e in container]))
        self.assertListEqual(sorted(uids), sorted([e for e in container.keys()]))

    def test_traversing(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category_lvl1 = createObject("ClassificationCategory")
        category_lvl1.identifier = "001"
        category_lvl1.title = "First"
        container._add_element(category_lvl1)

        category_lvl2 = createObject("ClassificationCategory")
        category_lvl2.identifier = "001.1"
        category_lvl2.title = "First"
        category_lvl1._add_element(category_lvl2)

        path = "folder/container/{0}".format(category_lvl1.UID())
        element = self.portal.restrictedTraverse(path)
        self.assertEqual("001", element.identifier)

        path += "/{0}".format(category_lvl2.UID())
        element = self.portal.restrictedTraverse(path)
        self.assertEqual("001.1", element.identifier)

    def test_container_modified(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        first = create_category(container, {"identifier": "001", "title": "First"})
        sub = create_category(first, {"identifier": "001.1", "title": "Sub"})
        self.assertEqual(2, len(iterate_over_tree_data(container)))
        self.assertEqual(1, len(iterate_over_tree_data(first)))
        # an addition in a sub-category refreshes the cached tree of all its parents
        create_category(sub, {"identifier": "001.1.1", "title": "Sub sub"})
        self.assertEqual(3, len(iterate_over_tree_data(container)))
        self.assertEqual(2, len(iterate_over_tree_data(first)))

    def test_category_modified(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        first = create_category(container, {"identifier": "001", "title": "First"})
        sub = create_category(first, {"identifier": "001.1", "title": "Sub"})
        self.assertEqual(
            ["001 - First", "001.1 - Sub"],
            sorted(d[1] for d in iterate_over_tree_data(container)),
        )
        sub.title = "Modified"
        first._update_element(sub)
        self.assertEqual(
            ["001 - First", "001.1 - Modified"],
            sorted(d[1] for d in iterate_over_tree_data(container)),
        )

    def test_category_deleted(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        used = create_category(container, {"identifier": "001", "title": "Used"}).UID()
        unused = create_category(
            container, {"identifier": "002", "title": "Unused"}
        ).UID()
        api.content.create(
            title="Mail",
            type="ClassifiedItem",
            container=self.folder,
            classification_categories=[used],
        )
        container.manage_delObjects([unused])
        self.assertNotIn(unused, container)
        transaction.commit()
        # a category used by a content is kept (the publisher aborts the transaction), with a message
        self.assertRaises(Redirect, container.manage_delObjects, [used])
        transaction.abort()
        self.assertIn(used, container)
        self.assertEqual(
            ["This category cannot be deleted because it is referenced elsewhere"],
            [m.message for m in IStatusMessage(self.layer["request"]).show()],
        )
