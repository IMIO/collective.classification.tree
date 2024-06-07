# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.classification.tree.testing import (
    COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING,
)  # noqa: E501

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that collective.classification.tree is properly installed."""

    layer = COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if collective.classification.tree is installed."""
        self.assertTrue(self.installer.isProductInstalled("collective.classification.tree"))

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
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstallProducts(["collective.classification.tree"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.classification.tree is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled("collective.classification.tree"))

    def test_browserlayer_removed(self):
        """Test that ICollectiveClassificationTreeLayer is removed."""
        from collective.classification.tree.interfaces import (
            ICollectiveClassificationTreeLayer,
        )
        from plone.browserlayer import utils

        self.assertNotIn(ICollectiveClassificationTreeLayer, utils.registered_layers())
