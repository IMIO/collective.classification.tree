# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from collective.classification.tree import utils
from operator import attrgetter
from plone import api
from zope.component import createObject

import unittest


class TestUtils(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(id="folder", type="Folder", container=self.portal)
        self.container = api.content.create(title="Container", type="ClassificationContainer", container=self.folder)
        structure = (
            (u"001", u"First", ((u"001.1", u"first"), (u"001.2", u"second"))),
            (u"002", u"Second", ((u"002.1", u"first"),)),
        )
        for id, title, subelements in structure:
            category = self._create_category(id, title)
            self.container._add_element(category)
            if subelements:
                for id, title in subelements:
                    subcategory = self._create_category(id, title)
                    category._add_element(subcategory)

    def tearDown(self):
        api.content.delete(self.folder)

    def _create_category(self, id, title):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        return category

    def test_get_parents(self):
        self.assertListEqual(utils.get_parents("-1.212.7"), [u"-1", u"-1.2", u"-1.21", u"-1.212", u"-1.212.7"])
        self.assertListEqual(
            utils.get_parents("-1.212.7/12"), [u"-1", u"-1.2", u"-1.21", u"-1.212", u"-1.212.7", u"-1.212.7/12"]
        )
        self.assertListEqual(utils.get_parents("-1.2./12"), [u"-1", u"-1.2", u"-1.2./12"])
        self.assertListEqual(utils.get_parents("-1.2..."), [u"-1", u"-1.2"])

    def test_iterate_over_tree_basic(self):
        """Ensure that returned results are correct"""
        results = utils.iterate_over_tree(self.container)
        self.assertEqual(5, len(results))

        expected = [u"001", u"001.1", u"001.2", u"002", u"002.1"]
        self.assertEqual(expected, sorted([e.identifier for e in results]))

    def test_iterate_over_tree_caching_first_level_addition(self):
        """Ensure that returned results are correctly cached"""
        results = utils.iterate_over_tree(self.container)
        self.assertEqual(5, len(results))

        new_category = self._create_category(u"003", u"Third")
        self.container._add_element(new_category)

        results = utils.iterate_over_tree(self.container)
        self.assertEqual(6, len(results))

        expected = [u"001", u"001.1", u"001.2", u"002", u"002.1", u"003"]
        self.assertEqual(expected, sorted([e.identifier for e in results]))

    def test_iterate_over_tree_caching_sub_level_addition(self):
        """Ensure that returned results are correctly cached"""
        results = utils.iterate_over_tree(self.container)
        self.assertEqual(5, len(results))

        new_category = self._create_category(u"002.2", u"second")
        container = [e for e in self.container.values() if e.identifier == u"002"][0]
        container._add_element(new_category)

        results = utils.iterate_over_tree(self.container)
        self.assertEqual(6, len(results))

        expected = [u"001", u"001.1", u"001.2", u"002", u"002.1", u"002.2"]
        self.assertEqual(expected, sorted([e.identifier for e in results]))

    def test_iterate_over_tree_caching_edition(self):
        """Ensure that returned results are correctly cached"""
        results = utils.iterate_over_tree(self.container)
        self.assertEqual(5, len(results))

        category = [e for e in self.container.values() if e.identifier == u"002"][0]
        category.identifier = u"002-updated"
        self.container._update_element(category)

        results = utils.iterate_over_tree(self.container)
        self.assertEqual(5, len(results))

        expected = [u"001", u"001.1", u"001.2", u"002-updated", u"002.1"]
        self.assertEqual(expected, sorted([e.identifier for e in results]))

    def test_importer_one_level(self):
        """Ensure that the content is correctly created"""
        container = api.content.create(title="Container2", type="ClassificationContainer", container=self.folder)
        _children = [
            {
                "identifier": u"key1.1",
                "title": u"Key 1.1",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
            {
                "identifier": u"key1.2",
                "title": u"Key 1.2",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
        ]
        utils.importer(container, None, u"key1", u"Key 1", None, None, _children)
        utils.importer(container, None, u"key2", u"Key 1", None, None, None)

        self.assertEqual(2, len(container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in container.values()]))

        subelement = container.get_by("identifier", "key1")
        self.assertEqual(2, len(subelement))
        self.assertEqual(["key1.1", "key1.2"], sorted([e.identifier for e in subelement.values()]))

    def test_importer_one_level_modified(self):
        """Ensure that the content is correctly modified"""
        container = self.container
        utils.importer(container, None, u"001", u"First Modified", None, None, None)
        utils.importer(container, None, u"002", u"Second", None, None, None)

        self.assertEqual(2, len(container))
        self.assertEqual(["001", "002"], sorted([e.identifier for e in container.values()]))

        subelement = container.get_by("identifier", "001")
        self.assertEqual(u"First Modified", subelement.title)
        self.assertEqual(2, len(subelement))
        self.assertEqual(["001.1", "001.2"], sorted([e.identifier for e in subelement.values()]))

    def test_importer_one_level_result(self):
        """Ensure that the returned list is correct"""
        container = api.content.create(title="Container2", type="ClassificationContainer", container=self.folder)
        _children = [
            {
                "identifier": u"key1.1",
                "title": u"Key 1.1",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
            {
                "identifier": u"key1.2",
                "title": u"Key 1.2",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
        ]
        modified = utils.importer(container, None, u"key1", u"Key 1", None, None, _children)
        expected_results = [
            [None],
            ["key1", None],
            ["key1", None],
        ]
        results = [[getattr(e, "identifier", None) for e in element] for element in modified]
        self.assertEqual(expected_results, results)

    def test_importer_one_level_modified_result(self):
        """Ensure that the returned list is correct"""
        container = self.container
        modified = utils.importer(container, None, u"001", u"First M", None, None, None)
        results = [[getattr(e, "identifier", None) for e in element] for element in modified]
        self.assertEqual([[None]], results)

        modified = utils.importer(container, None, u"002", u"Second", None, None, None)
        results = [[getattr(e, "identifier", None) for e in element] for element in modified]
        self.assertEqual([], results)

    def test_importer_multi_levels(self):
        """Ensure that the multi level contents is correctly created"""
        container = api.content.create(title="Container2", type="ClassificationContainer", container=self.folder)
        _children = [
            {
                "identifier": u"key1.1",
                "title": u"Key 1.1",
                "informations": None,
                "enabled": None,
                "_children": [
                    {
                        "identifier": u"key1.1.1",
                        "title": u"Key 1.1.1",
                        "informations": None,
                        "enabled": None,
                        "_children": [
                            {
                                "identifier": u"key1.1.1.1",
                                "title": u"Key 1.1.1.1",
                                "informations": None,
                                "enabled": None,
                                "_children": [],
                            },
                        ],
                    },
                ],
            },
            {
                "identifier": u"key1.2",
                "title": u"Key 1.2",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
        ]
        utils.importer(container, None, u"key1", u"Key 1", None, None, _children)
        utils.importer(container, None, u"key2", u"Key 1", None, None, None)

        self.assertEqual(2, len(container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in container.values()]))

        subelement = container.get_by("identifier", "key1")
        self.assertEqual(2, len(subelement))
        self.assertEqual(["key1.1", "key1.2"], sorted([e.identifier for e in subelement.values()]))

        subelement = subelement.get_by("identifier", "key1.1")
        self.assertEqual(1, len(subelement))
        self.assertEqual(["key1.1.1"], sorted([e.identifier for e in subelement.values()]))

        subelement = subelement.get_by("identifier", "key1.1.1")
        self.assertEqual(1, len(subelement))
        self.assertEqual(["key1.1.1.1"], sorted([e.identifier for e in subelement.values()]))

    def test_importer_multi_levels_modified(self):
        """Ensure that the content is correctly modified"""
        container = self.container
        children = [
            {
                "identifier": u"001.1",
                "title": u"first",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
            {
                "identifier": u"001.2",
                "title": u"second modified",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
        ]
        utils.importer(container, None, u"001", u"First Modified", None, None, children)

        self.assertEqual(2, len(container))
        self.assertEqual(["001", "002"], sorted([e.identifier for e in container.values()]))

        subelement = container.get_by("identifier", "001")
        self.assertEqual(u"First Modified", subelement.title)
        self.assertEqual(2, len(subelement))
        self.assertEqual(["001.1", "001.2"], sorted([e.identifier for e in subelement.values()]))
        self.assertEqual(["first", "second modified"], sorted([e.title for e in subelement.values()]))

    def test_importer_multi_levels_created_modified(self):
        """Ensure that the content is correctly created / modified"""
        container = self.container
        children = [
            {
                "identifier": u"001.1",
                "title": u"first",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
            {
                "identifier": u"001.2",
                "title": u"second modified",
                "informations": u"new infos",
                "enabled": False,
                "_children": [],
            },
            {
                "identifier": u"001.3",
                "title": u"new one",
                "informations": u"infos",
                "enabled": False,
                "_children": [],
            },
        ]
        utils.importer(container, None, u"001", u"First Modified", None, None, children)

        self.assertEqual(2, len(container))
        self.assertEqual(["001", "002"], sorted([e.identifier for e in container.values()]))

        subelement = container.get_by("identifier", "001")
        self.assertEqual(u"First Modified", subelement.title)
        self.assertEqual(3, len(subelement))
        values = sorted(subelement.values(), key=attrgetter("identifier"))
        self.assertEqual(["001.1", "001.2", "001.3"], [e.identifier for e in values])
        self.assertEqual([u"first", u"second modified", u"new one"], [e.title for e in values])
        self.assertEqual([None, u"new infos", u"infos"], [e.informations for e in values])
        self.assertEqual([True, False, False], [e.enabled for e in values])

    def test_importer_multi_levels_result(self):
        """Ensure that the returned list is correct"""
        container = api.content.create(title="Container2", type="ClassificationContainer", container=self.folder)
        _children = [
            {
                "identifier": u"key1.1",
                "title": u"Key 1.1",
                "informations": None,
                "enabled": None,
                "_children": [
                    {
                        "identifier": u"key1.1.1",
                        "title": u"Key 1.1.1",
                        "informations": None,
                        "enabled": None,
                        "_children": [
                            {
                                "identifier": u"key1.1.1.1",
                                "title": u"Key 1.1.1.1",
                                "informations": None,
                                "enabled": None,
                                "_children": [],
                            },
                        ],
                    },
                ],
            },
            {
                "identifier": u"key1.2",
                "title": u"Key 1.2",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
        ]
        modified = utils.importer(container, None, u"key1", u"Key 1", None, None, _children)
        expected_results = [
            [None],
            ["key1", None],
            ["key1.1", "key1", None],
            ["key1.1.1", "key1.1", "key1", None],
            ["key1", None],
        ]
        results = [[getattr(e, "identifier", None) for e in element] for element in modified]
        self.assertEqual(expected_results, results)

    def test_importer_multi_levels_modified_result(self):
        """Ensure that the returned list is correct"""
        container = self.container
        children = [
            {
                "identifier": u"001.1",
                "title": u"first",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
            {
                "identifier": u"001.2",
                "title": u"second modified",
                "informations": None,
                "enabled": None,
                "_children": [],
            },
        ]
        modified = utils.importer(container, None, u"001", u"First Modified", None, None, children)

        expected_results = [[None], ["001", None]]
        results = [[getattr(e, "identifier", None) for e in element] for element in modified]
        self.assertEqual(expected_results, results)

    def test_filter_chains_basic(self):
        data = [
            [None],
            ["key1", None],
            ["key1.1", "key1", None],
            ["key1.1.1", "key1.1", "key1", None],
            ["key1", None],
        ]
        result = utils.filter_chains(data)
        expected_results = ["key1.1.1"]
        self.assertEqual(result, expected_results)

    def test_filter_chains_complex(self):
        data = [
            [None],
            ["key1", None],
            ["key1.1", "key1", None],
            ["key1.1.1", "key1.1", "key1", None],
            ["key1.2", "key1", None],
            ["key1", None],
            ["key2", None],
            ["key3", None],
            ["key3.1", "key3", None],
        ]
        result = utils.filter_chains(data)
        expected_results = ["key1.1.1", "key1.2", "key2", "key3.1"]
        self.assertEqual(sorted(result), sorted(expected_results))

    def test_decimal_structure_basic(self):
        result = utils.generate_decimal_structure("1000")
        expected_results = {
            None: {
                u"1": (u"1", {u"enabled": False}),
            },
            u"1": {
                u"10": (u"10", {u"enabled": False}),
            },
            u"10": {
                u"100": (u"100", {u"enabled": False}),
            },
            u"100": {
                u"1000": (u"1000", {}),
            },
        }
        self.assertEqual(expected_results, result)

    def test_decimal_structure_with_basic_separator(self):
        """Ensure that separator are ignored during structure generation"""
        result = utils.generate_decimal_structure("10.0.0")
        expected_results = {
            None: {
                u"1": (u"1", {u"enabled": False}),
            },
            u"1": {
                u"10": (u"10", {u"enabled": False}),
            },
            u"10": {
                u"10.0": (u"10.0", {u"enabled": False}),
            },
            u"10.0": {
                u"10.0.0": (u"10.0.0", {}),
            },
        }
        self.assertEqual(expected_results, result)

    def test_decimal_structure_with_mixed_separator(self):
        """Ensure that mixed separator are ignored during structure generation"""
        result = utils.generate_decimal_structure("-1.073/074")
        expected_results = {
            None: {
                u"-1": (u"-1", {u"enabled": False}),
            },
            u"-1": {
                u"-1.0": (u"-1.0", {u"enabled": False}),
            },
            u"-1.0": {
                u"-1.07": (u"-1.07", {u"enabled": False}),
            },
            u"-1.07": {
                u"-1.073": (u"-1.073", {u"enabled": False}),
            },
            u"-1.073": {
                u"-1.073/074": (u"-1.073/074", {}),
            },
        }
        self.assertEqual(expected_results, result)

    def test_decimal_parent_basic(self):
        self.assertEqual("1", utils.get_decimal_parent("10"))
        self.assertEqual("10", utils.get_decimal_parent("100"))
        self.assertEqual("100", utils.get_decimal_parent("1000"))

    def test_decimal_parent_first_level(self):
        """Test when there is no parent for the given decimal code"""
        self.assertEqual(None, utils.get_decimal_parent("1"))
        self.assertEqual(None, utils.get_decimal_parent("."))
        self.assertEqual(None, utils.get_decimal_parent(".1"))
        self.assertEqual(None, utils.get_decimal_parent("/."))
        self.assertEqual(None, utils.get_decimal_parent("..1"))

    def test_decimal_parent_single_separator(self):
        """Test when the decimal code have a separator"""
        self.assertEqual("10", utils.get_decimal_parent("10.0"))
        self.assertEqual("10", utils.get_decimal_parent("10-0"))
        self.assertEqual("10", utils.get_decimal_parent("10/0"))
        self.assertEqual("10", utils.get_decimal_parent("10/073"))
        self.assertEqual("1.0", utils.get_decimal_parent("1.0.0"))
        self.assertEqual("1.0.0", utils.get_decimal_parent("1.0.0.0"))

    def test_decimal_parent_multi_separators(self):
        """Test when the decimal code have multiple separators"""
        self.assertEqual("1.0", utils.get_decimal_parent("1.0..0"))
        self.assertEqual("1.0", utils.get_decimal_parent("1.0./0"))
        self.assertEqual("1.0", utils.get_decimal_parent("1.0./073"))
        self.assertEqual("1.0", utils.get_decimal_parent("1.0-/0"))
