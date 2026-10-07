# -*- coding: utf-8 -*-
from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from collective.classification.tree.utils import iterate_over_tree_data
from plone import api
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import createObject

import unittest


class TestCategoriesView(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(
            id="folder", type="Folder", container=self.portal
        )

    def tearDown(self):
        api.content.delete(self.folder)

    def test_add_view_on_container(self):
        container = api.content.create(
            title="container", type="ClassificationContainer", container=self.folder
        )
        path = "container/add-ClassificationCategory"
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-title" in content)
        self.assertTrue("form-widgets-informations" in content)
        self.assertTrue(' id="form-buttons-add"' in content)
        self.assertTrue("Add Classification Category" in content)

    def test_add_view_on_category(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)

        path = "container/{0}/add-ClassificationCategory".format(category.UID())
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-title" in content)
        self.assertTrue("form-widgets-informations" in content)
        self.assertTrue(' id="form-buttons-add"' in content)
        self.assertTrue("Add Classification Category" in content)

    def test_view_on_category(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)
        path = "container/{0}/view".format(category.UID())
        view = container.restrictedTraverse(path)
        content = view()
        self.assertTrue("First" in content)
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-informations" in content)

    def test_edit_view_on_category(self):
        container = api.content.create(
            id="container", type="ClassificationContainer", container=self.folder
        )
        category = createObject("ClassificationCategory")
        category.identifier = "001"
        category.title = "First"
        container._add_element(category)

        path = "container/{0}/edit".format(category.UID())
        view = container.restrictedTraverse(path)
        self.assertTrue(isinstance(view, BrowserView))
        content = view()
        self.assertTrue("form-widgets-id" in content)
        self.assertTrue("form-widgets-title" in content)
        self.assertTrue("form-widgets-informations" in content)
        self.assertTrue(' id="form-buttons-save"' in content)
        self.assertTrue("Edit Classification Category" in content)


class TestCategoryAddForm(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test_handle_add(self):
        portal = self.layer["portal"]
        request = self.layer["request"]
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=portal
        )
        form = {
            "form.widgets.identifier": "001",
            "form.widgets.title": "First",
            "form.widgets.enabled": ["false"],
            "form.widgets.enabled-empty-marker": "1",
            "form.widgets.informations": "Info",
            "form.buttons.add": "Add",
        }
        testing.new_request(request, dict(form))
        container.restrictedTraverse("add-ClassificationCategory")()
        category = container.get_by("identifier", "001")
        self.assertEqual(
            ("First", False, "Info"),
            (category.title, category.enabled, category.informations),
        )
        self.assertEqual(
            ["Category added"], [m.message for m in IStatusMessage(request).show()]
        )
        # relative redirection (the new element is not wrapped): <container url>/<uid>/view in the browser
        self.assertTrue(
            request.response.getHeader("location").endswith(category.UID() + "/view")
        )
        # a sub-category, with an error first
        form.update({"form.widgets.identifier": "001.1", "form.widgets.title": ""})
        testing.new_request(request, dict(form))
        view = category.restrictedTraverse("add-ClassificationCategory")
        view()
        self.assertEqual(0, len(category))
        self.assertEqual(
            view.form_instance.formErrorsMessage, view.form_instance.status
        )
        form["form.widgets.title"] = "Sub"
        testing.new_request(request, dict(form))
        category.restrictedTraverse("add-ClassificationCategory")()
        self.assertEqual(
            [("001.1", "Sub")], [(e.identifier, e.title) for e in category.values()]
        )


class TestCategoryEditForm(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test_handle_save(self):
        portal = self.layer["portal"]
        request = self.layer["request"]
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=portal
        )
        category = container[
            create_category(container, {"identifier": "001", "title": "First"}).UID()
        ]
        self.assertEqual(
            ["001 - First"], [d[1] for d in iterate_over_tree_data(container)]
        )
        form = {
            "form.widgets.identifier": "001",
            "form.widgets.title": "Updated",
            "form.widgets.enabled": ["true"],
            "form.widgets.enabled-empty-marker": "1",
            "form.widgets.informations": "",
            "form.buttons.save": "Save",
        }
        testing.new_request(request, form)
        category.restrictedTraverse("edit")()
        self.assertEqual("Updated", container[category.UID()].title)
        self.assertEqual(
            ["Changes saved"], [m.message for m in IStatusMessage(request).show()]
        )
        self.assertEqual(
            category.absolute_url(), request.response.getHeader("location")
        )
        # the cached tree is refreshed by the modified event
        self.assertEqual(
            ["001 - Updated"], [d[1] for d in iterate_over_tree_data(container)]
        )
