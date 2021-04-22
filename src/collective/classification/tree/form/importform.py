# -*- coding: utf-8 -*-

from collective.classification.tree import _
from collective.classification.tree import utils
from persistent.dict import PersistentDict
from plone import api
from plone.autoform.form import AutoExtensibleForm
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from plone.z3cform.layout import FormWrapper
from time import time
from z3c.form import button
from z3c.form.form import Form
from z3c.form.interfaces import IFieldsForm
from zope import schema
from zope.annotation import IAnnotations
from zope.container.contained import ContainerModifiedEvent
from zope.interface import implementer
from zope.interface.interface import InterfaceClass

import csv


ANNOTATION_KEY = "collective.classification:import"


class BaseForm(AutoExtensibleForm, Form):
    def update(self):
        self.updateFieldsFromSchemata()
        self.updateWidgets()
        super(BaseForm, self).update()


class IImportFirstStep(model.Schema):

    source = NamedBlobFile(
        title=_(u"File"),
        description=_(u"CSV file that contains the classification tree"),
        required=True,
    )

    separator = schema.Choice(
        title=_(u"CSV Separator"),
        description=_(u"Separator character to use"),
        vocabulary="collective.classification.vocabularies:csv_separator",
        required=True,
    )


@implementer(IFieldsForm)
class ImportFormFirstStep(BaseForm):
    schema = IImportFirstStep
    ignoreContext = True
    # TODO:
    # - Ensure that the csv file contains the miminum number of columns
    # - Ensure that all lines of the csv file contains the same number of columns
    # - Detect encoding issues
    # - Return explicit error message containing line numbers

    def _set_data(self, data):
        annotation = IAnnotations(self.context)
        annotation[ANNOTATION_KEY] = PersistentDict()
        for key, value in data.items():
            annotation[ANNOTATION_KEY][key] = value

    @button.buttonAndHandler(_(u"Continue"), name="continue")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._set_data(data)
        redirect_url = u"{0}/@@import-process".format(self.context.absolute_url())
        self.request.response.redirect(redirect_url)


class ImportFirstStepView(FormWrapper):
    form = ImportFormFirstStep


@implementer(IFieldsForm)
class BaseImportFormSecondStep(BaseForm):
    """Baseclass for import form"""
    ignoreContext = True

    @property
    def _vocabulary(self):
        raise NotImplementedError("_vocabulary must be defined by subclass")

    @property
    def schema(self):
        """Generated schema based on csv file columns"""
        first_line = []
        data_lines = []
        has_header = False
        data = self._get_data()
        with data["source"].open() as f:
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(f.read(4096))
            f.seek(0)
            reader = csv.reader(f, delimiter=data["separator"].encode("utf-8"))
            first_line = reader.next()
            try:
                for i in range(0, 2):
                    data_lines.append(reader.next())
            except Exception:
                pass

        fields = []
        for idx, element in enumerate(first_line):
            if has_header:
                name = element
            else:
                name = str(idx + 1)
            sample = ", ".join(["'{0}'".format(l[idx]) for l in data_lines])

            fields.append(
                schema.Choice(
                    title=_("Column ${name}", mapping={"name": name}),
                    description=_("Sample data : ${data}", mapping={"data": sample}),
                    vocabulary=self._vocabulary,
                    required=False,
                )
            )
        return InterfaceClass(
            "IImportSecondStep",
            attrs={"column_{0}".format(idx): field for idx, field in enumerate(fields)},
        )

    def _get_data(self):
        annotation = IAnnotations(self.context)
        return annotation[ANNOTATION_KEY]

    def _process_data(self, data):
        """Return a list of dict containing object keys and a special key
        `_children` for hierarchy"""
        raise NotImplementedError("_process_data must be defined by subclass")

    def _process_csv(self, csv_reader, mapping, encoding, import_data):
        """Return a dict with every elements"""
        raise NotImplementedError("_process_csv must be defined by subclass")

    def _import_node(self, node):
        """Import a node (element with is children)"""
        raise NotImplementedError("_import_node must be defined by subclass")

    def _import(self, data):
        import_data = self._get_data()
        mapping = {int(k.replace("column_", "")): v for k, v in data.items()}
        encoding = "utf-8"
        with import_data["source"].open() as f:
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(f.read(4096))
            f.seek(0)
            reader = csv.reader(f, delimiter=import_data["separator"].encode(encoding))
            if has_header:
                reader.next()
            data = self._process_csv(reader, mapping, encoding, import_data)
            for node in self._process_data(data):
                self._import_node(node)

    @button.buttonAndHandler(_(u"Import"), name="import")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        begin = time()
        self._import(data)
        duration = int((time() - begin) * 100) / 100.0
        api.portal.show_message(
            message=_(
                u"Import completed in ${duration} seconds",
                mapping={"duration": str(duration)},
            ),
            request=self.request,
        )
        self.request.response.redirect(self.context.absolute_url())


class ImportFormSecondStep(BaseImportFormSecondStep):
    _vocabulary = u"collective.classification.vocabularies:categories_import_keys"
    # TODO:
    # - Ensure that all required columns are defined (identifier + name)
    # - Ensure that all required columns have values
    # - Return explicit error message containing line numbers

    def _process_data(self, data, key=None):
        """Consolidate data before import"""
        if key not in data:
            return []
        return [
            {
                "identifier": k,
                "title": v[0],
                "informations": v[1].get("informations"),
                "_children": self._process_data(data, key=k),
            }
            for k, v in data[key].items()
        ]

    def _process_csv(self, csv_reader, mapping, encoding, import_data):
        data = {}
        for line in csv_reader:
            line_data = {v: line[k].decode(encoding) for k, v in mapping.items()}
            parent_identifier = line_data.pop("parent_identifier") or None
            identifier = line_data.pop("identifier")
            title = line_data.pop("title")
            if parent_identifier not in data:
                # Using dictionary avoid duplicated informations
                data[parent_identifier] = {}
            data[parent_identifier][identifier] = (title, line_data)
        return data

    def _import_node(self, node):
        args = (None, node.pop("identifier"), node.pop("title"))
        modified = utils.importer(self.context, *args, **node)
        utils.trigger_event(modified, ContainerModifiedEvent)


class ImportSecondStepView(FormWrapper):
    form = ImportFormSecondStep

    def set_data(self, data):
        self.data = data
