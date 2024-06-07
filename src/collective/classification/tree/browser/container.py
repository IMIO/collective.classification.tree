# -*- coding: utf-8 -*-
from collective.classification.tree import caching
from plone.autoform.view import WidgetsView
from collective.classification.tree.contents.container import IClassificationContainer
from Products.Five import BrowserView


class ContainerView(WidgetsView):
    """Classification Container View"""

    schema = IClassificationContainer


class RefreshCache(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        caching.invalidate_cache("collective.classification.tree.utils.iterate_over_tree", self.context.UID())
        self.request.response.redirect(self.context.absolute_url())
