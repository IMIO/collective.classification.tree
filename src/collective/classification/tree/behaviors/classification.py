# -*- coding: utf-8 -*-

from collective.classification.tree import _
from collective.classification.tree.vocabularies import ClassificationTreeSourceBinder
from plone import schema
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.formwidget.autocomplete import AutocompleteMultiFieldWidget
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


class IClassificationCategoryMarker(Interface):
    pass


@provider(IFormFieldProvider)
class IClassificationCategory(model.Schema):
    """ """

    form.widget(classification_categories=AutocompleteMultiFieldWidget)
    classification_categories = schema.List(
        title=_(u"Classification Categories"),
        description=_(u"List of categories in which this content is filed"),
        value_type=schema.Choice(
            source=ClassificationTreeSourceBinder(enabled=True),
        ),
        required=False,
    )


@implementer(IClassificationCategory)
@adapter(IClassificationCategoryMarker)
class ClassificationCategory(object):
    def __init__(self, context):
        self.context = context

    @property
    def classification_categories(self):
        if hasattr(self.context, "classification_categories"):
            return self.context.classification_categories
        return None

    @classification_categories.setter
    def classification_categories(self, value):
        self.context.classification_categories = value
