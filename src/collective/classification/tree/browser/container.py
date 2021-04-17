# -*- coding: utf-8 -*-

from plone.autoform.view import WidgetsView
from collective.classification.tree.contents.container import IClassificationContainer


class ContainerView(WidgetsView):
    """Classification Container View"""
    schema = IClassificationContainer
