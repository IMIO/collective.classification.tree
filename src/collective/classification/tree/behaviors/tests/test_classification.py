# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.behaviors.classification import (
    IClassificationCategory,
)
from collective.classification.tree.behaviors.classification import (
    IClassificationCategoryMarker,
)
from collective.classification.tree.utils import create_category
from collective.classification.tree.vocabularies import ClassificationTreeSource
from lxml import html
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.autoform.interfaces import IFormFieldProvider

import json
import transaction
import unittest


class TestClassificationCategory(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.container = container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.portal
        )
        self.enabled = create_category(
            container, {"identifier": "001", "title": "Enabled"}
        ).UID()
        self.disabled = create_category(
            container, {"identifier": "002", "title": "Disabled", "enabled": False}
        ).UID()
        self.item = api.content.create(
            title="Mail", type="ClassifiedItem", container=self.portal
        )

    def test_classification_categories(self):
        # the field: a list of enabled categories, from the tree source
        self.assertTrue(IFormFieldProvider.providedBy(IClassificationCategory))
        self.assertTrue(IClassificationCategoryMarker.providedBy(self.item))
        field = IClassificationCategory["classification_categories"].bind(self.item)
        source = field.value_type.vocabulary
        self.assertIsInstance(source, ClassificationTreeSource)
        self.assertEqual(["001 - Enabled"], [t.title for t in source.search("abled")])
        # the adapter reads and writes the attribute of the content
        adapter = IClassificationCategory(self.item)
        self.assertIsNone(adapter.classification_categories)
        adapter.classification_categories = [self.enabled]
        self.assertEqual([self.enabled], self.item.classification_categories)
        self.assertEqual([self.enabled], adapter.classification_categories)

    def test_classification_categories_widget(self):
        """The select2 pattern searches the source through the widget URL"""
        create_category(self.container, {"identifier": "003", "title": "Ablation"})
        transaction.commit()
        browser = testing.Browser(self.layer["app"])
        browser.handleErrors = False
        browser.addHeader(
            "Authorization", "Basic {0}:{1}".format(TEST_USER_NAME, TEST_USER_PASSWORD)
        )
        browser.open(self.item.absolute_url() + "/@@edit")
        name = "form.widgets.IClassificationCategory.classification_categories"
        [widget] = html.fromstring(browser.contents).xpath(
            '//input[@name="{0}"]'.format(name)
        )
        url = json.loads(widget.get("data-pat-select2"))["vocabularyUrl"]
        self.assertTrue(url.endswith("/++widget++{0}/@@getSource".format(name)))
        browser.open(url + "?query=abl")
        # enabled categories only, ordered by match position
        self.assertEqual(
            ["003 - Ablation", "001 - Enabled"],
            [r["text"] for r in json.loads(browser.contents)["results"]],
        )
