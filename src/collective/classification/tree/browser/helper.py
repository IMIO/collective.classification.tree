# -*- coding: utf-8 -*-

from Products.Five.browser import BrowserView
from zope.interface import implementer
from zope.interface import Interface
from zope import schema


class IClassificationHelper(Interface):
    can_import = schema.Bool(title=u"Can import data", readonly=True)


@implementer(IClassificationHelper)
class ClassificationPublicHelper(BrowserView):
    def can_import(self):
        return False


@implementer(IClassificationHelper)
class ClassificationHelper(BrowserView):
    def can_import(self):
        return True
