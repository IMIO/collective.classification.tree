# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from plone import api
from plone.protect.authenticator import createToken
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getMultiAdapter

import unittest


class TestContextState(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test_actions(self):
        portal = self.layer["portal"]
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=portal
        )
        category = container[
            create_category(container, {"identifier": "001", "title": "First"}).UID()
        ]
        url = category.absolute_url()
        state = getMultiAdapter(
            (category, self.layer["request"]), name="plone_context_state"
        )
        # Actions menu: only delete
        self.assertEqual(["delete"], [a["id"] for a in state.actions("object_buttons")])
        # tabs
        self.assertEqual(
            [("view", url + "/view"), ("edit", url + "/edit")],
            [(a["id"], a["url"]) for a in state.actions("object")],
        )
        # user actions are kept, the others are dropped
        self.assertIn("logout", [a["id"] for a in state.actions("user")])
        self.assertEqual([], state.actions("document_actions"))


class TestDeleteConfirmationForm(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.portal
        )
        first = create_category(self.container, {"identifier": "001", "title": "First"})
        create_category(first, {"identifier": "001.1", "title": "Sub 1"})
        create_category(first, {"identifier": "001.2", "title": "Sub 2"})
        self.category = self.container[first.UID()]

    def _submit(self, button):
        testing.new_request(
            self.request,
            {
                "form.buttons.{0}".format(button): button,
                "_authenticator": createToken(),
            },
        )
        form = self.category.restrictedTraverse("delete_confirmation")
        form.update()
        return form

    def test_items_to_delete(self):
        form = self.category.restrictedTraverse("delete_confirmation")
        self.assertEqual(2, form.items_to_delete)
        content = form()
        self.assertIn(
            "Do you really want to delete this folder and all its contents?", content
        )
        self.assertIn('id="form-buttons-Delete"', content)
        self.assertIn('id="form-buttons-Cancel"', content)

    def test_handle_delete(self):
        self._submit("Delete")
        self.assertNotIn(self.category.UID(), self.container)
        self.assertEqual(
            ["001 - First has been deleted."],
            [m.message for m in IStatusMessage(self.request).show()],
        )
        self.assertEqual(
            self.container.absolute_url(), self.request.response.getHeader("location")
        )

    def test_handle_cancel(self):
        self._submit("Cancel")
        self.assertIn(self.category.UID(), self.container)
        self.assertTrue(
            self.request.response.getHeader("location").startswith(
                self.category.absolute_url()
            )
        )
