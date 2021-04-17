# -*- coding: utf-8 -*-

from operator import itemgetter
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from plone import api
from collective.classification.tree import utils


def classification_tree_vocabulary_factory(context):
    containers = api.content.find(portal_type="ClassificationContainer")
    results = []
    for container in containers:
        results.extend(
            [
                (e.UID(), e.Title())
                for e in utils.iterate_over_tree(container.getObject())
            ]
        )
    results = sorted(results, key=itemgetter(1))
    terms = [
        SimpleTerm(value=pair[0], token=pair[0], title=pair[1]) for pair in results
    ]
    return SimpleVocabulary(terms)
