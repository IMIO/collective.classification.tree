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
from z3c.form.datamanager import AttributeField
from z3c.form.form import Form
from z3c.form.interfaces import IFieldsForm
from zope import schema
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.container.contained import ContainerModifiedEvent
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import invariant
from zope.interface.interface import InterfaceClass

import copy
import csv
import re


ANNOTATION_KEY = "collective.classification:import"


class IGeneratedField(Interface):
    """
    Marker interface for generated interface field
    This is required for AttributeField adapter
    """


@implementer(IGeneratedField)
class GeneratedChoice(schema.Choice):
    pass


@implementer(IGeneratedField)
class GeneratedBool(schema.Bool):
    pass


class IImportFormView(Interface):
    """Marker interface for import form views"""


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

    has_header = schema.Bool(
        title=_(u"Include CSV header"),
        description=_(u"The CSV file contains an header row"),
        default=True,
        required=False,
    )

    @invariant
    def validate_csv_data(obj):
        return utils.validate_csv_data(obj)


class IImportSecondStepBase(Interface):
    @invariant
    def validate_columns(obj):
        return utils.validate_csv_columns(obj, ("identifier",))

    @invariant
    def validate_data(obj):
        annotations = IAnnotations(obj.__context__)
        format_dic = {}
        if obj._Data_data___.get("decimal_import", False):
            format_dic = {"identifier": r"(-?[./\d]+|( *, *)*)+$"}  # decimal format validation with multiple values
        return utils.validate_csv_content(
            obj,
            annotations[ANNOTATION_KEY],
            ("identifier",),
            format_dic,
        )

    decimal_import = GeneratedBool(
        title=_(u"Identifier are decimal codes"),
        default=True,
        required=False,
    )

    allow_empty = GeneratedBool(
        title=_(u"Allow empty column value"),
        default=False,
        required=False,
    )

    replace_slash = GeneratedBool(
        title=_(u"Replace slash in title"),
        default=True,
        required=False,
    )


@implementer(IFieldsForm)
class ImportFormFirstStep(BaseForm):
    schema = IImportFirstStep
    ignoreContext = True

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


@implementer(IImportFormView)
class ImportFirstStepView(FormWrapper):
    form = ImportFormFirstStep


@implementer(IFieldsForm)
class BaseImportFormSecondStep(BaseForm):
    """Baseclass for import form"""

    ignoreContext = False
    base_schema = IImportSecondStepBase

    @property
    def _vocabulary(self):
        raise NotImplementedError("_vocabulary must be defined by subclass")

    @property
    def schema(self):
        """Generated schema based on csv file columns"""
        first_line = []
        data_lines = []
        data = self._get_data()
        encoding = "utf-8"
        has_header = data["has_header"]
        with data["source"].open() as f:
            f.seek(0)
            reader = csv.reader(f, delimiter=data["separator"].encode(encoding))
            first_line = reader.next()
            try:
                for i in range(0, 2):
                    data_lines.append(reader.next())
            except Exception:
                pass

        fields = []
        for idx, element in enumerate(first_line):
            if has_header:
                name = element.decode(encoding)
            else:
                name = str(idx + 1)
            sample = u", ".join([u"'{0}'".format(ln[idx].decode(encoding)) for ln in data_lines])

            fields.append(
                GeneratedChoice(
                    title=_("Column ${name}", mapping={"name": name}),
                    description=_("Sample data : ${data}", mapping={"data": sample}),
                    vocabulary=self._vocabulary,
                    required=False,
                )
            )

        return InterfaceClass(
            "IImportSecondStep",
            attrs={"column_{0}".format(idx): field for idx, field in enumerate(fields)},
            bases=(self.base_schema,),
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

    def _before_import(self):
        """Method that is called before import process"""

    def _after_import(self):
        """Method that is called after import process"""

    def _import(self, data):
        self._before_import()
        # {'source': <plone.namedfile.file.NamedBlobFile object at ...>, 'has_header': True, 'separator': u';'}
        import_data = self._get_data()
        kwargs = {k: data.pop(k) for k in copy.deepcopy(data.keys()) if not k.startswith("column_")}
        mapping = {int(k.replace("column_", "")): v for k, v in data.items() if v}
        encoding = "utf-8"
        data = []
        with import_data["source"].open() as f:
            delimiter = import_data["separator"].encode(encoding)
            has_header = import_data["has_header"]
            f.seek(0)
            reader = csv.reader(f, delimiter=delimiter)
            if has_header:
                reader.next()
            data = self._process_csv(reader, mapping, encoding, import_data, **kwargs)
        for node in self._process_data(data):
            self._import_node(node)
        self._after_import()

    @button.buttonAndHandler(_(u"Import"), name="import")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._import(data)


class ImportFormSecondStep(BaseImportFormSecondStep):
    _vocabulary = u"collective.classification.vocabularies:categories_import_keys"

    def _process_data(self, data, key=None):
        """Consolidate data before import"""
        if key not in data:
            return []
        return [
            {
                "identifier": k,
                "title": v[0],
                "informations": v[1].get("informations"),
                "enabled": v[1].get("enabled"),
                "_children": self._process_data(data, key=k),
            }
            for k, v in data[key].items()
        ]

    def _generate_decimal_structure(self, data, identifier, enabled=False):
        structure = utils.generate_decimal_structure(identifier, enabled=enabled)
        for k, v in structure.items():
            if k not in data:
                data[k] = v
            else:
                for sk, sv in v.items():
                    if sk not in data[k]:
                        data[k][sk] = sv

    def _process_csv(self, csv_reader, mapping, encoding, import_data, decimal_import=False, **kw):
        data = {}
        for line in csv_reader:
            line_data = {v: line[k].decode(encoding) for k, v in mapping.items()}
            orig_identifier = line_data.pop("identifier") or None
            if not orig_identifier:
                continue
            title = line_data.pop("title", None)
            if title:
                title = title.strip()
                if kw.get("replace_slash", False):
                    title = title.replace("/", "-")
            if "enabled" in line_data:
                line_data["enabled"] = line_data["enabled"] and True or False
            for i, identifier in enumerate(re.split(" *, *", orig_identifier)):
                if decimal_import is True:
                    self._generate_decimal_structure(data, identifier)
                    parent_identifier = utils.get_decimal_parent(identifier)
                else:
                    parent_identifier = line_data.pop("parent_identifier", None) or None
                if not title or i:
                    title = identifier
                if parent_identifier not in data:
                    # Using dictionary avoid duplicated informations
                    data[parent_identifier] = {}
                # if exists, only update if title = identifier
                if identifier not in data[parent_identifier] or data[parent_identifier][identifier][0] == identifier:
                    data[parent_identifier][identifier] = (title, line_data)
        return data

    def _import_node(self, node):
        args = (None, node.pop("identifier"), node.pop("title"))
        modified = utils.importer(self.context, *args, **node)
        utils.trigger_event(modified, ContainerModifiedEvent)

    def _before_import(self):
        self.begin = time()

    def _after_import(self):
        duration = int((time() - self.begin) * 100) / 100.0
        api.portal.show_message(
            message=_(
                u"Import completed in ${duration} seconds",
                mapping={"duration": str(duration)},
            ),
            request=self.request,
        )
        self.request.response.redirect(self.context.absolute_url())


@implementer(IImportFormView)
class ImportSecondStepView(FormWrapper):
    form = ImportFormSecondStep

    def set_data(self, data):
        self.data = data


@adapter(Interface, IGeneratedField)
class GeneratedChoiceAttributeField(AttributeField):
    @property
    def adapted_context(self):
        return self.context

    def get(self):
        return
