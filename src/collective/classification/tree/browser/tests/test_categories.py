# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from zope.component import createObject
from Products.Five import BrowserView
from plone import api

import unittest


class TestCategoriesView(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(id="folder", type="Folder", container=self.portal)

    def tearDown(self):
        api.content.delete(self.folder)

    def test_add_view_on_container(self):
        container = api.content.create(title="container", type="ClassificationContainer", container=self.folder)
        path = "container/add-ClassificationCategory"
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-title" in content)
        self.assertTrue("form-widgets-informations" in content)
        self.assertTrue('input id="form-buttons-add"' in content)
        self.assertTrue("Add Classification Category" in content)

    def test_add_view_on_category(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)

        path = "container/{0}/add-ClassificationCategory".format(category.UID())
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-title" in content)
        self.assertTrue("form-widgets-informations" in content)
        self.assertTrue('input id="form-buttons-add"' in content)
        self.assertTrue("Add Classification Category" in content)

    def test_view_on_category(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)

        path = "container/{0}/view".format(category.UID())
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("First" in content)
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-informations" in content)

    def test_edit_view_on_category(self):
        container = api.content.create(id="container", type="ClassificationContainer", container=self.folder)
        category = createObject("ClassificationCategory")
        category.identifier = u"001"
        category.title = u"First"
        container._add_element(category)

        path = "container/{0}/edit".format(category.UID())
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-title" in content)
        self.assertTrue("form-widgets-informations" in content)
        self.assertTrue('input id="form-buttons-save"' in content)
        self.assertTrue("Edit Classification Category" in content)
