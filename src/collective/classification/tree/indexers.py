# -*- coding: utf-8 -*-

from Acquisition._Acquisition import aq_parent  # noqa
from collective.classification.tree.behaviors.classification import IClassificationCategoryMarker
from imio.helpers import EMPTY_STRING
from plone.indexer.decorator import indexer
from Products.CMFPlone.utils import base_hasattr


@indexer(IClassificationCategoryMarker)
def classification_categories_index(obj):
    """Indexer of"""
    if base_hasattr(obj, "classification_categories") and obj.classification_categories:
        return obj.classification_categories
    return [EMPTY_STRING]
