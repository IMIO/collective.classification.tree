# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.classification.tree.caching import forever_context_cache_key
from plone.memoize import ram
from zope.component import createObject


@ram.cache(forever_context_cache_key)
def iterate_over_tree(obj):
    """Iterate over an object to get all sub objects"""
    result = []
    for e in obj.values():
        result.append(e)
        if len(e) > 0:
            result.extend(iterate_over_tree(e))
    return result


def get_by(context, identifier, key):
    filtered = [e for e in iterate_over_tree(context) if getattr(e, identifier) == key]
    if len(filtered) > 0:
        return filtered[0]


def get_chain(obj, include_self=True):
    """Return Acquisition chain for classification object"""
    in_chain = True
    chain = []
    if include_self is True:
        chain.append(obj)
    portal_types = ("ClassificationContainer", "ClassificationCategory")
    while in_chain is True:
        obj = aq_parent(obj)
        if not obj or obj.portal_type not in portal_types:
            in_chain = False
            break
        else:
            chain.append(obj)
    return chain


def importer(context, identifier, title, parent_identifier=None, informations=None):
    parent = context
    if parent_identifier:
        parent = get_by(context, "identifier", parent_identifier) or context

    element = parent.get_by("identifier", identifier)
    exist = True
    has_change = False
    if element is None:
        exist = False
        element = createObject("ClassificationCategory")
        element.identifier = identifier

    if element.title != title:
        element.title = title
        has_change = True
    if element.informations != informations:
        element.informations = informations
        has_change = True

    if exist is True and has_change is True:
        parent._update_element(element)
    elif exist is False:
        parent._add_element(element)
