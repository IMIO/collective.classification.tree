# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree.services.tree import TreeSearchHandler
from collective.classification.tree.utils import create_category
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from six.moves.urllib.parse import urlencode

import json
import transaction
import unittest


def datatables_query(**kwargs):
    """Query sent by the datatables listing of container.pt"""
    query = {
        "draw": "1",
        "columns[0][data]": "identifier",
        "columns[0][searchable]": "true",
        "columns[1][data]": "title",
        "columns[1][searchable]": "true",
        "columns[2][data]": "informations",
        "columns[2][searchable]": "true",
        "columns[3][data]": "enabled",
        "columns[3][searchable]": "false",
        "columns[4][data]": "links",
        "columns[4][searchable]": "false",
        "order[0][column]": "0",
        "order[0][dir]": "asc",
        "start": "0",
        "length": "25",
        "search[value]": "",
        "search[regex]": "true",
    }
    query.update(kwargs)
    return query


class TestTreeSearchHandler(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.container = api.content.create(title="Container", type="ClassificationContainer", container=self.portal)
        self.first = self.container[create_category(self.container, {"identifier": u"001", "title": u"First"}).UID()]
        create_category(
            self.first, {"identifier": u"001.1", "title": u"Première sous-catégorie", "informations": u"info"}
        )
        create_category(self.container, {"identifier": u"002", "title": u"Second", "informations": u"Archives"})
        create_category(self.container, {"identifier": u"003", "title": u"Third", "enabled": False})
        self.handler = TreeSearchHandler(self.container)

    def _search(self, **kwargs):
        total, filtered, data = self.handler.search(datatables_query(**kwargs))
        return total, filtered, [e.identifier for e in data]

    def test_search(self):
        self.assertEqual((4, 4, [u"001", u"001.1", u"002", u"003"]), self._search())
        self.assertEqual((4, 4, [u"001.1", u"002"]), self._search(start="1", length="2"))
        self.assertEqual((4, 1, [u"001.1"]), self._search(**{"search[value]": "sous"}))

    def test__limits(self):
        self.handler.query = {}
        self.assertEqual((0, 10), self.handler._limits)
        self.handler.query = {"start": "5", "length": "20"}
        self.assertEqual((5, 25), self.handler._limits)
        self.handler.query = {"start": "x", "length": "y"}
        self.assertEqual((0, 10), self.handler._limits)

    def test__to_int(self):
        self.assertEqual(3, TreeSearchHandler._to_int("3", 0))
        self.assertEqual(7, TreeSearchHandler._to_int("abc", 7))

    def test__get_columns(self):
        self.handler.query = datatables_query()
        self.assertEqual(["identifier", "title", "informations", "enabled", "links"], self.handler._get_columns())
        self.assertEqual(["identifier", "title", "informations"], self.handler._get_columns(searchable=True))
        self.handler.query = {}
        self.assertEqual([], self.handler._get_columns())

    def test__filter(self):
        # no search: everything
        self.assertEqual(4, self._search()[1])
        # regex: substring, case and accent insensitive, on the searchable columns
        self.assertEqual([u"001.1"], self._search(**{"search[value]": "PREMIERE"})[2])
        self.assertEqual([u"002"], self._search(**{"search[value]": "archiv"})[2])
        self.assertEqual([u"001", u"001.1"], self._search(**{"search[value]": "001"})[2])
        # not searchable column (enabled)
        self.assertEqual([], self._search(**{"search[value]": "False"})[2])
        # no regex: whole value
        self.assertEqual([u"002"], self._search(**{"search[value]": "second", "search[regex]": "false"})[2])
        self.assertEqual([], self._search(**{"search[value]": "sec", "search[regex]": "false"})[2])

    def test__object_filter(self):
        category = self.container.get_by("identifier", u"002")
        self.assertTrue(TreeSearchHandler._object_filter(category, ["title"], u"eco", True))
        self.assertFalse(TreeSearchHandler._object_filter(category, ["title"], u"eco", False))
        self.assertTrue(TreeSearchHandler._object_filter(category, ["title"], u"second", False))
        self.assertFalse(TreeSearchHandler._object_filter(category, ["identifier"], u"second", True))

    def test__order(self):
        self.assertEqual([u"003", u"002", u"001.1", u"001"], self._search(**{"order[0][dir]": "desc"})[2])
        # by title (column 1)
        self.assertEqual([u"001", u"001.1", u"002", u"003"], self._search(**{"order[0][column]": "1"})[2])
        # no column: iteration order
        self.handler.query = {}
        results = self.container.values()
        self.assertEqual(results, self.handler._order(results))

    @testing.plone6_bug
    def test__order_none_values(self):
        """Ordering by a column with empty values (informations): TypeError on Python 3"""
        self.handler.query = datatables_query(**{"order[0][column]": "2"})
        results = self.handler._order(self.container.values() + self.first.values())
        self.assertEqual([None, None, u"Archives", u"info"], [e.informations for e in results])


class TestTreeGet(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.container = api.content.create(title="Container", type="ClassificationContainer", container=self.portal)
        self.first = self.container[create_category(self.container, {"identifier": u"001", "title": u"First"}).UID()]
        create_category(self.first, {"identifier": u"001.1", "title": u"Sub"})
        create_category(self.container, {"identifier": u"002", "title": u"Second"})
        transaction.commit()
        self.browser = testing.Browser(self.layer["app"])
        self.browser.handleErrors = False
        self.browser.addHeader("Accept", "application/json")
        self.browser.addHeader("Authorization", "Basic {0}:{1}".format(TEST_USER_NAME, TEST_USER_PASSWORD))

    def _get(self, obj, **kwargs):
        self.browser.open("{0}/@tree?{1}".format(obj.absolute_url(), urlencode(datatables_query(**kwargs))))
        return json.loads(self.browser.contents)

    def test_reply(self):
        result = self._get(self.container, **{"search[value]": "00"})
        self.assertEqual("1", result["draw"])
        self.assertEqual(3, result["recordsTotal"])
        self.assertEqual(3, result["recordsFiltered"])
        self.assertEqual([u"001", u"001.1", u"002"], [e["identifier"] for e in result["data"]])
        self.assertEqual(self.first.absolute_url(), result["data"][0]["@id"])
        # on a category: its sub-categories
        result = self._get(self.first)
        self.assertEqual(1, result["recordsTotal"])
        self.assertEqual([u"Sub"], [e["title"] for e in result["data"]])
