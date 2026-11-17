# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from lxml import html
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD

import json
import transaction
import unittest


class TestSourceAjaxSelectWidget(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        portal = self.layer["portal"]
        container = api.content.create(
            title="Container", type="ClassificationContainer", container=portal
        )
        self.uid = create_category(
            container, {"identifier": "001", "title": "First"}
        ).UID()
        # "deleted": a category removed since the content was filed
        self.item = api.content.create(
            title="Mail",
            type="ClassifiedItem",
            container=portal,
            classification_categories=[self.uid, "deleted"],
        )
        transaction.commit()
        self.browser = testing.Browser(self.layer["app"])
        self.browser.handleErrors = False
        self.browser.addHeader(
            "Authorization", "Basic {0}:{1}".format(TEST_USER_NAME, TEST_USER_PASSWORD)
        )

    def test_get_vocabulary(self):
        """The view shows the category titles (the source terms)"""
        self.browser.open(self.item.absolute_url())
        badges = html.fromstring(self.browser.contents).xpath(
            '//span[@id="form-widgets-IClassificationCategory-classification_categories"]'
            "/span[@data-token]"
        )
        self.assertEqual(
            [(self.uid, "001 - First"), ("deleted", "deleted")],
            [(b.get("data-token"), b.text) for b in badges],
        )

    def test_get_pattern_options(self):
        """The edit form gives select2 the titles of the selected categories"""
        self.browser.open(self.item.absolute_url() + "/@@edit")
        [widget] = html.fromstring(self.browser.contents).xpath(
            '//input[@name="form.widgets.IClassificationCategory.classification_categories"]'
        )
        options = json.loads(widget.get("data-pat-select2"))
        self.assertEqual(
            {self.uid: "001 - First", "deleted": "deleted"}, options["initialValues"]
        )
        self.assertEqual("{0};deleted".format(self.uid), widget.get("value"))
