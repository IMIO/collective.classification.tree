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

import csv
import unittest


class TestImportForm(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.folder = api.content.create(id="folder", type="Folder", container=self.portal)
        self.container = api.content.create(title="Container", type="ClassificationContainer", container=self.folder)

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
            "has_header": False,
        }
        form._set_data(data)
        annotations = IAnnotations(self.container)
        self.assertTrue(importform.ANNOTATION_KEY in annotations)

        annotation = annotations[importform.ANNOTATION_KEY]
        self.assertEqual(data["separator"], annotation["separator"])
        self.assertEqual(data["source"], annotation["source"])
        self.assertEqual(data["has_header"], annotation["has_header"])

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
            "form.widgets.has_header": u"False",
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
            "form.widgets.has_header": u"False",
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual("CSV file must contains at least 2 columns", errors[0].error.message)

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
            "form.widgets.has_header": u"False",
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
            [u"猫", u"èè", u"ùù"],
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
            "form.widgets.has_header": u"True",
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual("File encoding is not utf8", errors[0].error.message)

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
            "form.widgets.has_header": u"False",
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
            "form.widgets.has_header": u"False",
        }
        form = importform.ImportFormFirstStep(self.container, request)
        form.update()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertTrue("Lines 2, 3" in translate(errors[0].error.message))

    def test_second_step_basic_encoding(self):
        """Ensure that form can be displayed even with special characters"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["null", "key1", "key1.1", "Key 1.1", "informations"],
            [
                "null",
                "",
                u"key1 éà$€".encode("utf8"),
                u"Key 1 éà$€".encode("utf8"),
                u"informations éà$€".encode("utf8"),
            ],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        exception = None
        try:
            form.update()
        except UnicodeDecodeError as e:
            exception = e
        self.assertIsNone(exception)

    def test_second_step_basic_delimiter(self):
        """Test edge case related to csv delimiter"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u","
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["key1", "key1.1", '"Key 1,1"'],
            ["key1.1", "key1.1.1", '"Key 1.1.1"'],
        ]
        for line in lines:
            csv.write(",".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        exception = None
        try:
            form.update()
        except Exception as e:
            exception = e
        self.assertIsNone(exception)

    def test_second_step_import_basic(self):
        """Test importing csv data"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
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
            "decimal_import": False,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in self.container.values()]))

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

    def test_second_step_import_single_column(self):
        """Test importing csv data"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["", "key2", "Key 2"],
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
            "column_0": None,
            "column_1": "identifier",
            "column_2": None,
            "decimal_import": False,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in self.container.values()]))
        self.assertEqual(["key1", "key2"], sorted([e.title for e in self.container.values()]))

    def test_second_step_import_encoding(self):
        """Test importing csv data with special chars in header and content"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = True
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            [u"猫".encode("utf8"), u"èè".encode("utf8"), u"ùù".encode("utf8")],
            ["", u"kéy1".encode("utf8"), u"Kèy 1".encode("utf8")],
            [u"kéy1".encode("utf8"), u"kéy1.1".encode("utf8"), u"猫".encode("utf8")],
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
            "decimal_import": False,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(1, len(self.container))
        self.assertEqual([u"kéy1"], [e.identifier for e in self.container.values()])

        key1 = self.container.get_by("identifier", u"kéy1")
        self.assertEqual(1, len(key1))
        self.assertEqual([u"kéy1.1"], [e.identifier for e in key1.values()])

        key1_1 = key1.get_by("identifier", u"kéy1.1")
        self.assertEqual(u"猫", key1_1.title)

    def test_second_step_import_encoding_form(self):
        """Test importing csv data with special chars in header and content"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = True
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            [u"猫".encode("utf8"), u"èè".encode("utf8"), u"ùù".encode("utf8")],
            ["", u"kéy1".encode("utf8"), u"Kèy 1".encode("utf8")],
            [u"kéy1".encode("utf8"), u"kéy1.1".encode("utf8"), u"猫".encode("utf8")],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form.update()
        exception = None
        try:
            render = form.render()
        except UnicodeDecodeError as e:
            exception = e
        self.assertIsNone(exception)
        self.assertTrue(u"Column {0}".format(u"猫") in render)

    def test_second_step_import_decimal_basic(self):
        """Test importing csv data with decimal codes"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["100", "Key 1"],
            ["100.1", "Key 1.1"],
            ["100.2", "Key 1.2"],
            ["200", "Key 2"],
            ["200.1", "Key 2.1"],
            ["200.10", "Key 2.10"],
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
            "column_0": "identifier",
            "column_1": "title",
            "decimal_import": True,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(["1", "2"], sorted([e.identifier for e in self.container.values()]))

        code_1 = self.container.get_by("identifier", "1")
        self.assertEqual("1", code_1.title)
        self.assertEqual(1, len(code_1))
        self.assertEqual(["10"], [e.identifier for e in code_1.values()])

        code_10 = code_1.get_by("identifier", "10")
        self.assertEqual("10", code_10.title)
        self.assertEqual(1, len(code_10))
        self.assertEqual(["100"], [e.identifier for e in code_10.values()])

        code_100 = code_10.get_by("identifier", "100")
        self.assertEqual("Key 1", code_100.title)
        self.assertEqual(2, len(code_100))
        self.assertEqual(
            ["100.1", "100.2"],
            sorted([e.identifier for e in code_100.values()]),
        )
        self.assertEqual(
            ["Key 1.1", "Key 1.2"],
            sorted([e.title for e in code_100.values()]),
        )

        code_2 = self.container.get_by("identifier", "2")
        self.assertEqual("2", code_2.title)
        self.assertEqual(1, len(code_2))
        self.assertEqual(["20"], [e.identifier for e in code_2.values()])

        code_20 = code_2.get_by("identifier", "20")
        self.assertEqual("20", code_20.title)
        self.assertEqual(1, len(code_20))
        self.assertEqual(["200"], [e.identifier for e in code_20.values()])

        code_200 = code_20.get_by("identifier", "200")
        self.assertEqual("Key 2", code_200.title)
        self.assertEqual(1, len(code_200))
        self.assertEqual(["200.1"], [e.identifier for e in code_200.values()])

        code_2001 = code_200.get_by("identifier", "200.1")
        self.assertEqual("Key 2.1", code_2001.title)
        self.assertEqual(1, len(code_2001))
        self.assertEqual(["200.10"], [e.identifier for e in code_2001.values()])
        self.assertEqual(["Key 2.10"], [e.title for e in code_2001.values()])

    def test_second_step_import_extra_columns(self):
        """Test importing csv data"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
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
            "decimal_import": False,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in self.container.values()]))

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
        annotation["has_header"] = False
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
            "decimal_import": False,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in self.container.values()]))

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
        annotation["has_header"] = False
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
            "decimal_import": False,
            "allow_empty": False,
        }
        form._import(data)
        self.assertEqual(2, len(self.container))
        self.assertEqual(["key1", "key2"], sorted([e.identifier for e in self.container.values()]))

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

    def test_second_step_required_columns_ok(self):
        """Test validation of required columns"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"parent_identifier",
            "form.widgets.column_1": u"identifier",
            "form.widgets.column_2": u"title",
            "form.widgets.decimal_import": u"False",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        annotation["source"] = NamedBlobFile(
            data=self._csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_second_step_required_columns_nok(self):
        """Test validation of required columns"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"--NOVALUE--",
            "form.widgets.column_1": u"--NOVALUE--",
            "form.widgets.column_2": u"--NOVALUE--",
            "form.widgets.decimal_import": u"False",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        annotation["source"] = NamedBlobFile(
            data=self._csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual(
            "The following required columns are missing: identifier",
            translate(errors[0].error.message),
        )

    def test_second_step_required_columns_data_ok(self):
        """Test validation of required columns data"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"parent_identifier",
            "form.widgets.column_1": u"identifier",
            "form.widgets.column_2": u"title",
            "form.widgets.decimal_import": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        annotation["source"] = NamedBlobFile(
            data=self._csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_second_step_required_columns_data_nok(self):
        """Test validation of required columns data"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"parent_identifier",
            "form.widgets.column_1": u"identifier",
            "form.widgets.column_2": u"title",
            "form.widgets.decimal_import": u"False",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["key1", "key1.1", "Key 1.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1"],
            ["key1", "", "Key 1.2"],
            ["key1", "key1.3", ""],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual(
            "Lines 4 have missing required value(s)",
            translate(errors[0].error.message),
        )

    def test_second_step_required_columns_data_nok_allow_empty(self):
        """Test validation of required columns data"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"parent_identifier",
            "form.widgets.column_1": u"identifier",
            "form.widgets.column_2": u"title",
            "form.widgets.decimal_import": u"False",
            "form.widgets.allow_empty": u"selected",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1"],
            ["key1", "key1.1", "Key 1.1"],
            ["key1.1", "key1.1.1", "Key 1.1.1"],
            ["key1", "", "Key 1.2"],
            ["key1", "key1.3", ""],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_second_step_columns_data_format_nok(self):
        """Test validation of columns data format"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"identifier",
            "form.widgets.column_1": u"title",
            "form.widgets.decimal_import": u"selected",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["-1", "key1"],
            [".10", "key2"],
            ["-1.1", "key3"],
            ["-1 11", "Key4"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(1, len(errors))
        self.assertEqual(
            "Bad format values: Line 4, col 1: '-1 11'",
            translate(errors[0].error.message),
        )

    def test_second_step_columns_data_format_ok(self):
        """Test validation of columns data format"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"identifier",
            "form.widgets.column_1": u"title",
            "form.widgets.decimal_import": u"selected",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["-1", "key1"],
            [".10", "key2"],
            ["-1.1", "key3"],
            ["-1.11,.12", "Key4"],
            ["-1.13 ,.13", "Key5"],
            ["-1.14, .14", "Key6"],
            ["-1.15 , .15, 1.20.21", "Key7"],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_second_step_optional_columns_data_ok(self):
        """Test validation of optional columns data"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"parent_identifier",
            "form.widgets.column_1": u"identifier",
            "form.widgets.column_2": u"title",
            "form.widgets.column_3": u"informations",
            "form.widgets.decimal_import": u"False",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1", "infos"],
            ["key1", "key1.1", "Key 1.1", ""],
            ["key1.1", "key1.1.1", "Key 1.1.1", ""],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_second_step_optional_columns_data_ok(self):
        """Test validation of optional columns data"""
        request = self.layer["request"]
        request.form = {
            "form.buttons.import": u"Importer",
            "form.widgets.column_0": u"parent_identifier",
            "form.widgets.column_1": u"identifier",
            "form.widgets.column_2": u"title",
            "form.widgets.column_3": u"informations",
            "form.widgets.decimal_import": u"False",
            "form.widgets.allow_empty": u"False",
        }
        annotations = IAnnotations(self.container)
        annotation = annotations[importform.ANNOTATION_KEY] = PersistentDict()
        annotation["has_header"] = False
        annotation["separator"] = u";"
        csv = StringIO()
        lines = [
            ["", "key1", "Key 1", "infos"],
            ["key1", "key1.1", "Key 1.1", ""],
            ["key1.1", "key1.1.1", "Key 1.1.1", ""],
        ]
        for line in lines:
            csv.write(";".join(line) + "\n")
        csv.seek(0)
        annotation["source"] = NamedBlobFile(
            data=csv.read(),
            contentType=u"text/csv",
            filename=u"test.csv",
        )
        form = importform.ImportFormSecondStep(self.container, request)
        form.updateFieldsFromSchemata()
        form.updateWidgets()
        data, errors = form.extractData()
        self.assertEqual(0, len(errors))

    def test_process_data_basic(self):
        """Tests _process_data with basic data structure"""
        form = importform.ImportFormSecondStep(self.container, self.layer["request"])
        data = {
            None: {u"key1": (u"Key 1", {}), u"key2": (u"Key 2", {})},
            u"key1": {u"key1.1": (u"Key 1.1", {}), u"key1.2": (u"Key 1.2", {"enabled": True})},
            u"key2": {u"key2.1": (u"Key 2.1", {}), u"key2.2": (u"Key 2.2", {"enabled": False})},
        }
        expected_results = [
            {
                "identifier": u"key1",
                "title": u"Key 1",
                "informations": None,
                "enabled": None,
                "_children": [
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
                        "enabled": True,
                        "_children": [],
                    },
                ],
            },
            {
                "identifier": u"key2",
                "title": u"Key 2",
                "informations": None,
                "enabled": None,
                "_children": [
                    {
                        "identifier": u"key2.1",
                        "title": u"Key 2.1",
                        "informations": None,
                        "enabled": None,
                        "_children": [],
                    },
                    {
                        "identifier": u"key2.2",
                        "title": u"Key 2.2",
                        "informations": None,
                        "enabled": False,
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
            None: {u"key1": (u"Key 1", {}), u"key2": (u"Key 2", {"enabled": False})},
            u"key1": {u"key1.1": (u"Key 1.1", {}), u"key1.2": (u"Key 1.2", {})},
            u"key2": {u"key2.1": (u"Key 2.1", {"enabled": False})},
            u"key1.1": {u"key1.1.1": (u"Key 1.1.1", {})},
            u"key1.1.1": {u"key1.1.1.1": (u"Key 1.1.1.1", {})},
        }
        expected_results = [
            {
                "identifier": u"key1",
                "title": u"Key 1",
                "informations": None,
                "enabled": None,
                "_children": [
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
                ],
            },
            {
                "identifier": u"key2",
                "title": u"Key 2",
                "informations": None,
                "enabled": False,
                "_children": [
                    {
                        "identifier": u"key2.1",
                        "title": u"Key 2.1",
                        "informations": None,
                        "enabled": False,
                        "_children": [],
                    },
                ],
            },
        ]
        processed_data = form._process_data(data)
        self.assertEqual(self._sort_processed_data(processed_data), expected_results)

    def test_process_csv_replace_slash(self):
        """Test _process_csv with csv data that contains slashes"""
        form = importform.ImportFormSecondStep(self.container, {})
        _csv = StringIO()
        lines = [
            ["1", "First/level"],
            ["11", "Second / level"],
            ["12", "Other / level / in // Tesla"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "identifier",
            "column_1": "title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, decimal_import=True, replace_slash=True)
        expected_result = {
            None: {u"1": (u"First-level", {})},
            u"1": {u"11": (u"Second - level", {}), u"12": (u"Other - level - in -- Tesla", {})},
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_multiple_identifiers(self):
        """Test _process_csv with csv data that contains multiple identifiers"""
        form = importform.ImportFormSecondStep(self.container, {})
        _csv = StringIO()
        lines = [
            ["1", "First level"],
            ["11", "Second level"],
            ["11, 12", "Other level in / Tesla"],
            ["21, 22", "New sub levels"],
            ["111", "Yet one"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "identifier",
            "column_1": "title",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, decimal_import=True, replace_slash=True)
        expected_result = {
            None: {
                u"1": (u"First level", {}),
                u"2": (u"2", {u"enabled": False}),
            },
            u"1": {u"11": (u"Second level", {}), u"12": (u"12", {})},
            u"11": {u"111": (u"Yet one", {})},
            u"2": {u"21": (u"New sub levels", {}), u"22": (u"22", {})},
        }
        self.assertEqual(expected_result, result)

    def test_process_csv_enabled(self):
        """Test _process_csv with enabled column"""
        form = importform.ImportFormSecondStep(self.container, {})
        _csv = StringIO()
        lines = [
            ["1", "First/level", ""],
            ["11", "Second / level", "0"],
            ["12", "Other / level / in // Tesla", "1"],
            ["20", "Sublevel without parent", "1"],
        ]
        for line in lines:
            _csv.write(";".join(line) + "\n")
        _csv.seek(0)
        reader = csv.reader(_csv, delimiter=";")
        data = {
            "column_0": "identifier",
            "column_1": "title",
            "column_2": "enabled",
        }
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        result = form._process_csv(reader, mapping, "utf-8", {}, decimal_import=True, replace_slash=True)
        expected_result = {
            None: {
                u"1": (u"First-level", {"enabled": False}),
                u"2": (u"2", {"enabled": False}),
            },
            u"1": {
                u"11": (u"Second - level", {"enabled": True}),
                u"12": (u"Other - level - in -- Tesla", {"enabled": True}),
            },
            u"2": {
                u"20": (u"Sublevel without parent", {"enabled": True}),
            },
        }
        self.assertEqual(expected_result, result)
