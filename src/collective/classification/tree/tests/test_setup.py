# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.classification.tree.testing import (  # noqa: E501
    COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.base.utils import get_installer

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.classification.tree is properly installed."""

    layer = COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if collective.classification.tree is installed."""
        self.assertTrue(
            self.installer.is_product_installed("collective.classification.tree")
        )

    def test_restapi_installed(self):
        """The listing calls @tree: "Use REST API" for every role"""
        self.assertTrue(self.installer.is_product_installed("plone.restapi"))

    def test_browserlayer(self):
        """Test that ICollectiveClassificationTreeLayer is registered."""
        from collective.classification.tree.interfaces import (
            ICollectiveClassificationTreeLayer,
        )
        from plone.browserlayer import utils

        self.assertIn(ICollectiveClassificationTreeLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer = get_installer(self.portal, self.layer["request"])
        self.installer.uninstall_product("collective.classification.tree")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.classification.tree is cleanly uninstalled."""
        self.assertFalse(
            self.installer.is_product_installed("collective.classification.tree")
        )

    def test_browserlayer_removed(self):
        """Test that ICollectiveClassificationTreeLayer is removed."""
        from collective.classification.tree.interfaces import (
            ICollectiveClassificationTreeLayer,
        )
        from plone.browserlayer import utils

        self.assertNotIn(ICollectiveClassificationTreeLayer, utils.registered_layers())
