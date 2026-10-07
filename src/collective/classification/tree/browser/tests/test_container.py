# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from collective.classification.tree.utils import iterate_over_tree_data
from plone import api

import unittest


class TestContainerView(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test_view(self):
        portal = self.layer["portal"]
        container = api.content.create(title="My tree", type="ClassificationContainer", container=portal)
        content = container.restrictedTraverse("@@view")()
        self.assertIn("My tree</h1>", content)
        self.assertIn('data-url="{0}/@tree"'.format(container.absolute_url()), content)
        self.assertIn('<table id="table"', content)
        for header in ("Identifier", "Name", "Informations", "Enabled"):
            self.assertIn("<th>{0}</th>".format(header), content)
        self.assertIn('$("#table").DataTable({', content)


class TestRefreshCache(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test___call__(self):
        portal = self.layer["portal"]
        container = api.content.create(title="Container", type="ClassificationContainer", container=portal)
        create_category(container, {"identifier": u"001", "title": u"First"})
        self.assertEqual(1, len(iterate_over_tree_data(container)))
        # added without event: the cached tree is stale
        create_category(container, {"identifier": u"002", "title": u"Second"}, event=False)
        self.assertEqual(1, len(iterate_over_tree_data(container)))
        container.restrictedTraverse("@@refresh-cache")()
        self.assertEqual(2, len(iterate_over_tree_data(container)))
        self.assertEqual(container.absolute_url(), self.layer["request"].response.getHeader("location"))
