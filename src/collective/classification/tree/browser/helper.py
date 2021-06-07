# -*- coding: utf-8 -*-

from Products.Five.browser import BrowserView
from zope.interface import implementer
from zope.interface import Interface
from zope import schema


class IClassificationHelper(Interface):
    can_import = schema.Bool(title=u"Can import data", readonly=True)
    can_add_category = schema.Bool(title=u"Can add a new category", readonly=True)


@implementer(IClassificationHelper)
class ClassificationPublicHelper(BrowserView):
    def can_import(self):
        return False

    def can_add_category(self):
        return False


@implementer(IClassificationHelper)
class ClassificationContainerHelper(ClassificationPublicHelper):
    def can_import(self):
        return True

    def can_add_category(self):
        return True


@implementer(IClassificationHelper)
class ClassificationCategoryHelper(ClassificationPublicHelper):
    def can_add_category(self):
        return True
