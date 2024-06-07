# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.classification.tree import _
from collective.classification.tree.caching import forever_context_cache_key
from plone.memoize import ram
from zope.component import createObject
from zope.event import notify
from zope.interface import Invalid

import csv
import re

# DECIMAL_SEPARATORS = ("-", ".", ";", "/", "|", ":")
DECIMAL_SEPARATORS = ("-", ".", "/")


@ram.cache(forever_context_cache_key)
def iterate_over_tree(obj):
    """Iterate over an object to get all sub objects"""
    result = []
    for e in obj.values():
        result.append(e)
        if len(e) > 0:
            result.extend(iterate_over_tree(e))
    return result


def create_category(parent, data, event=True):
    """Create a category object.
    :param parent: container to add object
    :param data: dictionary containing fields and values
    :param event: boolean to choose to notify event
    :rtype: object
    """
    element = createObject("ClassificationCategory")
    for key, value in data.items():
        setattr(element, key, value)
    parent._add_element(element, event=event)
    return element


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


def get_parents(code):
    """Get parents based on a decimal code"""
    levels = []
    level = ""
    for i, char in enumerate(code):
        level = u"{0}{1}".format(level, char)
        if char == u"/":  # we stop when encoutering /
            levels.append(u"{}{}".format(level, code[i + 1 :]))
            break
        elif char in DECIMAL_SEPARATORS:
            continue
        else:
            levels.append(level)
    return levels


def generate_decimal_structure(code, enabled=False):
    """Generate a structure based on a decimal code.

    If it contains / the parent is considered only before the /"""
    levels = get_parents(code)
    results = {}
    last_element = None
    for level in levels:
        if level == code:  # current elem
            results[last_element] = {level: (level, {})}
        else:
            results[last_element] = {level: (level, {u"enabled": enabled})}
        last_element = level
    return results


def get_decimal_parent(code):
    """Return the parent decimal code from a given code e.g. 100 from 100.1"""
    level = lastparent = ""
    for i, char in enumerate(code[:-1]):
        level = u"{0}{1}".format(level, char)
        if char == u"/":  # we stop when encoutering /
            break
        elif char in DECIMAL_SEPARATORS:
            continue
        else:
            lastparent = level
    return lastparent or None


def importer(context, parent_identifier, identifier, title, informations=None, enabled=None, _children=None):
    """
    Expected structure for _children (iterable) with dict element that contains :
        * identifier (String)
        * title (String)
        * informations (String) or None
        * enabled (Bool) or None
        * _children (Iterable of dicts)

    Return a set with chain of elements that were added or updated
    """
    parent = context
    if parent_identifier:
        parent = get_by(context, "identifier", parent_identifier) or context

    modified = []
    modified.extend(element_importer(parent, identifier, title, informations, enabled, _children))
    return modified


def element_importer(parent, identifier, title, informations, enabled, children):
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
    if informations is not None and element.informations != informations:
        element.informations = informations
        has_change = True
    if enabled is not None and element.enabled != enabled:
        element.enabled = enabled
        has_change = True

    modified = []
    if exist is True and has_change is True:
        parent._update_element(element, event=False)
        modified.append(get_chain(parent))
    elif exist is False:
        parent._add_element(element, event=False)
        modified.append(get_chain(parent))

    if children:
        for child in children:
            args = (
                element,
                child["identifier"],
                child["title"],
                child["informations"],
                child["enabled"],
                child["_children"],
            )
            modified.extend(element_importer(*args))
    return modified


def filter_chains(elements):
    """Filter elements from chains"""
    result = []
    raw_result = []
    for chain in sorted(elements, key=lambda x: len(x), reverse=True):
        if len(chain) > 1:
            head, tail = chain[0], chain[1:]
        else:
            head, tail = chain[0], []
        if head not in result and head not in raw_result:
            result.append(head)
            raw_result.extend(tail)
    return result


def trigger_event(chains, eventcls, excluded=[]):
    """Trigger the event only once for each element"""
    for element in filter_chains(chains):
        notify(eventcls(element))


def validate_csv_data(obj, min_length=2):
    source, separator = [obj._Data_data___.get(k) for k in ("source", "separator")]
    with source.open() as f:
        try:
            f.read().decode("utf8")
        except UnicodeDecodeError:
            raise Invalid(_("File encoding is not utf8"))
    with source.open() as f:
        reader = csv.reader(f, delimiter=separator.encode("utf-8"))
        first_line = reader.next()
        if len(first_line) < 2:
            raise Invalid(_("CSV file must contains at least 2 columns"))
        base_length = len(first_line)

        wrong_lines = [str(i + 2) for i, v in enumerate(reader) if len(v) != base_length]
        if wrong_lines:
            raise Invalid(
                _(
                    "Lines ${lines} does not contains the same number of element",
                    mapping={"lines": ", ".join(wrong_lines)},
                )
            )
    return True


def validate_csv_columns(obj, required_columns):
    """Verify that all required columns are present"""
    columns = [v for k, v in obj._Data_data___.items() if k.startswith("column_")]
    missing_columns = []
    for column in required_columns:
        if column not in columns:
            missing_columns.append(column)
    if len(missing_columns) > 0:
        raise Invalid(
            _(
                "The following required columns are missing: ${columns}",
                mapping={"columns": ", ".join(missing_columns)},
            )
        )
    return True


def validate_csv_content(obj, annotation, required_columns, format_dic={}):
    """Verify csv content:

    * check if all required columns have values
    * check some columns format with re pattern {'identifier': pattern}
    """
    columns = {v: int(k.replace("column_", "")) for k, v in obj._Data_data___.items() if k.startswith("column_") and v}
    if not columns:
        # Validation of columns is made by another function
        return True
    separator = annotation["separator"]
    has_header = annotation["has_header"]
    source = annotation["source"]
    with source.open() as f:
        reader = csv.reader(f, delimiter=separator.encode("utf-8"))
        base_idx = 1
        if has_header:
            base_idx += 1
            reader.next()
        expected_length = len(required_columns)
        wrong_lines = []
        wrong_values = []
        for idx, line in enumerate(reader):
            if not getattr(obj, "allow_empty", False):  # option only in tree import
                values = [line[columns[n]] for n in required_columns if line[columns[n]]]
                if len(values) != expected_length:
                    wrong_lines.append(str(idx + base_idx))
            for col in format_dic:
                val = line[columns[col]]
                if not re.match(format_dic[col], val):
                    wrong_values.append("Line {}, col {}: '{}'".format(idx + base_idx, columns[col] + 1, val))
        if wrong_lines:
            raise Invalid(
                _(
                    "Lines ${lines} have missing required value(s)",
                    mapping={"lines": ", ".join(wrong_lines)},
                )
            )
        if wrong_values:
            raise Invalid(_("Bad format values: ${errors}", mapping={"errors": " || ".join(wrong_values)}))
    return True
