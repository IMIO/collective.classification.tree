# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from plone import api

import unittest


CLASSIFICATION_ACTIONS = ["classification.import", "classification.tree.add", "classification.tree.refresh_cache"]


def classification_actions(obj):
    """Ids of the package object_buttons actions available on obj"""
    actions = api.portal.get_tool("portal_actions").listFilteredActionsFor(obj).get("object_buttons", [])
    return sorted([a["id"] for a in actions if a["id"].startswith("classification.")])


class TestClassificationPublicHelper(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.helper = self.portal.restrictedTraverse("@@classification_helper")

    def test_can_import(self):
        self.assertFalse(self.helper.can_import())
        self.assertEqual([], classification_actions(self.portal))

    def test_can_add_category(self):
        self.assertFalse(self.helper.can_add_category())


class TestClassificationContainerHelper(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        portal = self.layer["portal"]
        self.container = api.content.create(title="Container", type="ClassificationContainer", container=portal)
        self.helper = self.container.restrictedTraverse("@@classification_helper")

    def test_can_import(self):
        self.assertTrue(self.helper.can_import())
        self.assertEqual(CLASSIFICATION_ACTIONS, classification_actions(self.container))

    def test_can_add_category(self):
        self.assertTrue(self.helper.can_add_category())


class TestClassificationCategoryHelper(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test_can_add_category(self):
        portal = self.layer["portal"]
        container = api.content.create(title="Container", type="ClassificationContainer", container=portal)
        category = container[create_category(container, {"identifier": u"001", "title": u"First"}).UID()]
        helper = category.restrictedTraverse("@@classification_helper")
        self.assertTrue(helper.can_add_category())
        self.assertFalse(helper.can_import())
        self.assertEqual(["classification.tree.add"], classification_actions(category))
