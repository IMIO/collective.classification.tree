# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.utils import create_category
from collective.classification.tree.utils import iterate_over_tree_data
from plone import api

import unittest


class TestContainer(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test_container_modified(self):
        container = api.content.create(title="Container", type="ClassificationContainer", container=self.layer["portal"])
        first = create_category(container, {"identifier": u"001", "title": u"First"})
        self.assertEqual([u"001 - First"], [d[1] for d in iterate_over_tree_data(container)])
        # the cached tree is not refreshed without event
        create_category(container, {"identifier": u"002", "title": u"Second"}, event=False)
        self.assertEqual(1, len(iterate_over_tree_data(container)))
        # deletion (ContainerModifiedEvent)
        del container[first.UID()]
        self.assertEqual([u"002 - Second"], [d[1] for d in iterate_over_tree_data(container)])
