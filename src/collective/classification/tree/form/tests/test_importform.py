# -*- coding: utf-8 -*-

from StringIO import StringIO
from ZPublisher.HTTPRequest import FileUpload
from collective.classification.tree import testing
from collective.classification.tree.form import importform
from operator import itemgetter
from persistent.dict import PersistentDict
from plone import api
from plone.namedfile import NamedBlobFile
from zope.annotation import IAnnotations
from zope.component import createObject
from zope.i18n import translate

import unittest


class TestImportForm(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(
            id="folder", type="Folder", container=self.portal
        )
        self.container = api.content.create(
            title="Container", type="ClassificationContainer", container=self.folder
        )

    def tearDown(self):
        api.content.delete(self.folder)

    def _create_category(self, id, title):
        category = createObject("ClassificationCategory")
        category.identifier = id
        category.title = title
        return category

    @property
    def _csv(self):
        """Return a fake csv with data"""
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["key1", "key1.1", "Key 1.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1"],
            ["key1", "key1.2", "Key 1.2"],
            ["key1", "key1.3", "Key 1.3"],
            ["", "key2", "Key 2"],
            ["key2", "key2.1", "Key 2.1"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        return csv

    def _sort_processed_data(self, data):
        """Ensure that processed data are correctly sorted before comparison"""
        data = sorted(data, key=itemgetter("identifier"))
        for element in data:
            if not element["_children"]:
                continue
            element["_children"] = self._sort_processed_data(element["_children"])
        return data

    def test_first_step_set_data(self):
        form = importform.ImportFormFirstStep(self.container, self.layer["request"])
        data = {
            "source": NamedBlobFile(
                data=self._csv.read(),
                contentType=u"text/csv",
                filename=u"test.csv",
            ),
            "separator": u";",
        }
        form._set_data(data)
        annotations = IAnnotations(self.container)
        self.assertTrue(importform.ANNOTATION_KEY in annotations)

        annotation = annotations[importform.ANNOTATION_KEY]
        self.assertEqual(data["separator"], annotation["separator"])
        self.assertEqual(data["source"], annotation["source"])

    def test_first_step_validate_columns_number_correct(self):
        """Ensure that csv file contains at least 2 columns"""
        request = self.layer["request"]
        source = FileUpload(
            type(
                "obj",
                (object,),
                {"file": self._csv, "filename": "foo.csv", "headers": "text/csv"},
            )()
        )
        request.form = {
            "form.buttons.continue": u"Continuer",
            "form.widgets.separator": [u";"],
            "form.widgets.separator-empty-marker": u"1",
            "form.widgets.source": source,
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_first_step_validate_columns_number_nok(self):
        """Ensure that csv file contains at least 2 columns"""
        request = self.layer["request"]
        csv = StringIO()
        lines = [
            [""],
            ["key1"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        source = FileUpload(
            type(
                "obj",
                (object,),
                {"file": csv, "filename": "foo.csv", "headers": "text/csv"},
            )()
        )
        request.form = {
            "form.buttons.continue": u"Continuer",
            "form.widgets.separator": [u";"],
            "form.widgets.separator-empty-marker": u"1",
            "form.widgets.source": source,
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual(
            "CSV file must contains at least 2 columns", errors[0].error.message
        )

    def test_first_step_validate_csv_encoding_ok(self):
        """Ensure that we can decode csv file"""
        request = self.layer["request"]
        source = FileUpload(
            type(
                "obj",
                (object,),
                {"file": self._csv, "filename": "foo.csv", "headers": "text/csv"},
            )()
        )
        request.form = {
            "form.buttons.continue": u"Continuer",
            "form.widgets.separator": [u";"],
            "form.widgets.separator-empty-marker": u"1",
            "form.widgets.source": source,
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_first_step_validate_csv_encoding_nok(self):
        """Ensure that we can decode csv file"""
        request = self.layer["request"]
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            [u"猫", u"ààà", u"ééé"],
        ]
        for line in lines:
            csv.write(";".join(line).encode("utf-16") + "\n")
        csv.seek(0)
        source = FileUpload(
            type(
                "obj",
                (object,),
                {"file": csv, "filename": "foo.csv", "headers": "text/csv"},
            )()
        )
        request.form = {
            "form.buttons.continue": u"continuer",
            "form.widgets.separator": [u";"],
            "form.widgets.separator-empty-marker": u"1",
            "form.widgets.source": source,
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual(
            "File encoding is not utf8", errors[0].error.message
        )

    def test_first_step_validate_line_columns_ok(self):
        """Ensure that every lines have the same number of columns"""
        request = self.layer["request"]
        source = FileUpload(
            type(
                "obj",
                (object,),
                {"file": self._csv, "filename": "foo.csv", "headers": "text/csv"},
            )()
        )
        request.form = {
            "form.buttons.continue": u"continuer",
            "form.widgets.separator": [u";"],
            "form.widgets.separator-empty-marker": u"1",
            "form.widgets.source": source,
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_first_step_validate_line_columns_nok(self):
        """Ensure that every lines have the same number of columns"""
        request = self.layer["request"]
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["key1", "key1.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1", "foo"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        source = FileUpload(
            type(
                "obj",
                (object,),
                {"file": csv, "filename": "foo.csv", "headers": "text/csv"},
            )()
        )
        request.form = {
            "form.buttons.continue": u"continuer",
            "form.widgets.separator": [u";"],
            "form.widgets.separator-empty-marker": u"1",
            "form.widgets.source": source,
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertTrue("Lines 2, 3" in translate(errors[0].error.message))

    def test_second_step_import_basic(self):
        """Test importing csv data"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["separator"] = u";"
        annotation["source"] = NamedBlobFile(
            data=self._csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        data = {
            "column_0": "parent_identifier",
            "column_1": "identifier",
            "column_2": "title",
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(
            ["key1", "key2"], sorted([e.identifier for e in self.container.values()])
        )

        key1 = self.container.get_by("identifier", "key1")
        self.assertEqual(3, len(key1))
        self.assertEqual(
            ["key1.1", "key1.2", "key1.3"],
            sorted([e.identifier for e in key1.values()]),
        )

        key1_1 = key1.get_by("identifier", "key1.1")
        self.assertEqual(1, len(key1_1))
        self.assertEqual(["key1.1.1"], sorted([e.identifier for e in key1_1.values()]))

        key2 = self.container.get_by("identifier", "key2")
        self.assertEqual(1, len(key2))
        self.assertEqual(["key2.1"], sorted([e.identifier for e in key2.values()]))

    def test_second_step_import_extra_columns(self):
        """Test importing csv data"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["null", "", "key1", "Key 1", "informations", ""],
            ["null", "key1", "key1.1", "Key 1.1", "informations", ""],
            ["null", "key1.1", "key1.1.1", "Key 1.1.1", "informations", ""],
            ["null", "key1", "key1.2", "Key 1.2", "informations", ""],
            ["null", "key1", "key1.3", "Key 1.3", "informations", ""],
            ["null", "", "key2", "Key 2", "informations", ""],
            ["null", "key2", "key2.1", "Key 2.1", "informations", ""],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        data = {
            "column_1": "parent_identifier",
            "column_2": "identifier",
            "column_3": "title",
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(
            ["key1", "key2"], sorted([e.identifier for e in self.container.values()])
        )

        key1 = self.container.get_by("identifier", "key1")
        self.assertEqual(3, len(key1))
        self.assertEqual(
            ["key1.1", "key1.2", "key1.3"],
            sorted([e.identifier for e in key1.values()]),
        )

        key1_1 = key1.get_by("identifier", "key1.1")
        self.assertEqual(1, len(key1_1))
        self.assertEqual(["key1.1.1"], sorted([e.identifier for e in key1_1.values()]))

        key2 = self.container.get_by("identifier", "key2")
        self.assertEqual(1, len(key2))
        self.assertEqual(["key2.1"], sorted([e.identifier for e in key2.values()]))

    def test_second_step_import_order(self):
        """Test importing csv data were order is not logic"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["key1", "key1.1", "Key 1.1"],
            ["key1", "key1.3", "Key 1.3"],
            ["", "key2", "Key 2"],
            ["key1", "key1.2", "Key 1.2"],
            ["key2", "key2.1", "Key 2.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        data = {
            "column_0": "parent_identifier",
            "column_1": "identifier",
            "column_2": "title",
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(
            ["key1", "key2"], sorted([e.identifier for e in self.container.values()])
        )

        key1 = self.container.get_by("identifier", "key1")
        self.assertEqual(3, len(key1))
        self.assertEqual(
            ["key1.1", "key1.2", "key1.3"],
            sorted([e.identifier for e in key1.values()]),
        )

        key1_1 = key1.get_by("identifier", "key1.1")
        self.assertEqual(1, len(key1_1))
        self.assertEqual(["key1.1.1"], sorted([e.identifier for e in key1_1.values()]))

        key2 = self.container.get_by("identifier", "key2")
        self.assertEqual(1, len(key2))
        self.assertEqual(["key2.1"], sorted([e.identifier for e in key2.values()]))

    def test_second_step_import_duplicate(self):
        """Test importing csv data were there is duplicated values"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["", "key1", "Key 1"],
            ["", "key1", "Key 1"],
            ["", "key1", "Key 1"],
            ["key1", "key1.1", "Key 1.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1"],
            ["key1", "key1.2", "Key 1.2"],
            ["key1", "key1.3", "Key 1.3"],
            ["key1", "key1.3", "Key 1.3"],
            ["key1", "key1.3", "Key 1.3"],
            ["", "key2", "Key 2"],
            ["", "key2", "Key 2"],
            ["key2", "key2.1", "Key 2.1"],
            ["key2", "key2.1", "Key 2.1"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        data = {
            "column_0": "parent_identifier",
            "column_1": "identifier",
            "column_2": "title",
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(
            ["key1", "key2"], sorted([e.identifier for e in self.container.values()])
        )

        key1 = self.container.get_by("identifier", "key1")
        self.assertEqual(3, len(key1))
        self.assertEqual(
            ["key1.1", "key1.2", "key1.3"],
            sorted([e.identifier for e in key1.values()]),
        )

        key1_1 = key1.get_by("identifier", "key1.1")
        self.assertEqual(1, len(key1_1))
        self.assertEqual(["key1.1.1"], sorted([e.identifier for e in key1_1.values()]))

        key2 = self.container.get_by("identifier", "key2")
        self.assertEqual(1, len(key2))
        self.assertEqual(["key2.1"], sorted([e.identifier for e in key2.values()]))

    def test_process_data_basic(self):
        """Tests _process_data with basic data structure"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        data = {
            None: {u"key1": (u"Key 1", {}), u"key2": (u"Key 2", {})},
            u"key1": {u"key1.1": (u"Key 1.1", {}), u"key1.2": (u"Key 1.2", {})},
            u"key2": {u"key2.1": (u"Key 2.1", {}), u"key2.2": (u"Key 2.2", {})},
        }
        expected_results = [
            {
                "identifier": u"key1",
                "title": u"Key 1",
                "informations": None,
                "_children": [
                    {
                        "identifier": u"key1.1",
                        "title": u"Key 1.1",
                        "informations": None,
                        "_children": [],
                    },
                    {
                        "identifier": u"key1.2",
                        "title": u"Key 1.2",
                        "informations": None,
                        "_children": [],
                    },
                ],
            },
            {
                "identifier": u"key2",
                "title": u"Key 2",
                "informations": None,
                "_children": [
                    {
                        "identifier": u"key2.1",
                        "title": u"Key 2.1",
                        "informations": None,
                        "_children": [],
                    },
                    {
                        "identifier": u"key2.2",
                        "title": u"Key 2.2",
                        "informations": None,
                        "_children": [],
                    },
                ],
            },
        ]
        processed_data = form._process_data(data)
        self.assertEqual(self._sort_processed_data(processed_data), expected_results)

    def test_process_data_multilevel(self):
        """Tests _process_data with multi levels data structure"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        data = {
            None: {u"key1": (u"Key 1", {}), u"key2": (u"Key 2", {})},
            u"key1": {u"key1.1": (u"Key 1.1", {}), u"key1.2": (u"Key 1.2", {})},
            u"key2": {u"key2.1": (u"Key 2.1", {})},
            u"key1.1": {u"key1.1.1": (u"Key 1.1.1", {})},
            u"key1.1.1": {u"key1.1.1.1": (u"Key 1.1.1.1", {})},
        }
        expected_results = [
            {
                "identifier": u"key1",
                "title": u"Key 1",
                "informations": None,
                "_children": [
                    {
                        "identifier": u"key1.1",
                        "title": u"Key 1.1",
                        "informations": None,
                        "_children": [
                            {
                                "identifier": u"key1.1.1",
                                "title": u"Key 1.1.1",
                                "informations": None,
                                "_children": [
                                    {
                                        "identifier": u"key1.1.1.1",
                                        "title": u"Key 1.1.1.1",
                                        "informations": None,
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
                        "_children": [],
                    },
                ],
            },
            {
                "identifier": u"key2",
                "title": u"Key 2",
                "informations": None,
                "_children": [
                    {
                        "identifier": u"key2.1",
                        "title": u"Key 2.1",
                        "informations": None,
                        "_children": [],
                    },
                ],
            },
        ]
        processed_data = form._process_data(data)
        self.assertEqual(self._sort_processed_data(processed_data), expected_results)
