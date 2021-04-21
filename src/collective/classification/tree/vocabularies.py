# -*- coding: utf-8 -*-

from collective.classification.tree import _
from collective.classification.tree import utils
from operator import itemgetter
from plone import api
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def iterable_to_vocabulary(values):
    return SimpleVocabulary(
        [SimpleTerm(value=pair[0], token=pair[0], title=pair[1]) for pair in values]
    )


def classification_tree_vocabulary_factory(context):
    query = {"portal_type": "ClassificationContainer", "context": api.portal.get()}
    containers = api.content.find(**query)
    results = []
    for container in containers:
        results.extend(
            [
                (e.UID(), e.Title())
                for e in utils.iterate_over_tree(container.getObject())
            ]
        )
    results = sorted(results, key=itemgetter(1))
    return iterable_to_vocabulary(results)


def csv_separator_vocabulary_factory(context):
    values = (
        (u";", u";"),
        (u",", u","),
        (u"|", u"|"),
        (u"	", _(u"tab")),  # ! value is a tab not a whitespace !
        (u" ", _(u"whitespace")),
    )
    return iterable_to_vocabulary(values)


def import_keys_vocabulary_factory(context):
    values = (
        (u"parent_identifier", _(u"Parent Identifier")),
        (u"identifier", _(u"Identifier")),
        (u"title", _(u"Name")),
        (u"informations", _(u"Informations")),
    )
    return iterable_to_vocabulary(values)
