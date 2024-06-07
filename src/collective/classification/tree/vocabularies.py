# -*- coding: utf-8 -*-

from collective.classification.tree import _
from collective.classification.tree import utils
from imio.helpers.vocabularies import EnhancedTerm
from operator import itemgetter
from plone import api
from unidecode import unidecode
from z3c.form import util
from z3c.form.i18n import MessageFactory as _zf
from z3c.formwidget.query.interfaces import IQuerySource
from zope.interface import implementer
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def iterable_to_vocabulary(values):
    return SimpleVocabulary([SimpleTerm(value=pair[0], token=pair[0], title=pair[1]) for pair in values])


def category_iterable_to_vocabulary(values):
    return SimpleVocabulary(
        [EnhancedTerm(value=pair[0], token=pair[0], title=pair[1], enabled=pair[2]) for pair in values]
    )


def classification_tree_vocabulary_factory(context):
    query = {"portal_type": "ClassificationContainer", "context": api.portal.get()}
    containers = api.content.find(**query)
    results = []
    for container in containers:
        results.extend([(e.UID(), e.Title(), e.enabled) for e in utils.iterate_over_tree(container.getObject())])
    results = sorted(results, key=itemgetter(1))
    return category_iterable_to_vocabulary(results)


def full_classification_tree_vocabulary_factory(context):
    query = {"portal_type": "ClassificationContainer"}
    containers = context.portal_catalog.unrestrictedSearchResults(**query)
    results = []
    for container in containers:
        results.extend(
            [(e.UID(), e.Title(), e.enabled) for e in utils.iterate_over_tree(container._unrestrictedGetObject())]
        )
    results = sorted(results, key=itemgetter(1))
    return category_iterable_to_vocabulary(results)


def classification_tree_id_mapping_vocabulary_factory(context):
    query = {"portal_type": "ClassificationContainer", "context": api.portal.get()}
    containers = api.content.find(**query)
    results = []
    for container in containers:
        results.extend([(e.identifier, e.UID()) for e in utils.iterate_over_tree(container.getObject())])
    results = sorted(results, key=itemgetter(1))
    return iterable_to_vocabulary(results)


def classification_tree_title_mapping_vocabulary_factory(context):
    query = {"portal_type": "ClassificationContainer", "context": api.portal.get()}
    containers = api.content.find(**query)
    results = []
    for container in containers:
        results.extend([(e.title, e.UID()) for e in utils.iterate_over_tree(container.getObject())])
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
        (u"enabled", _(u"Enabled")),
    )
    return iterable_to_vocabulary(values)


@implementer(IQuerySource)
class ClassificationTreeSource(object):
    def __init__(self, context, enabled=None):
        self.context = context
        self._vocabulary = None
        self.enabled = enabled

    def __contains__(self, term):
        return self.vocabulary.__contains__(term)

    def __iter__(self):
        return self.vocabulary.__iter__()

    def __len__(self):
        return self.vocabulary.__len__()

    @property
    def _verified_user(self):
        """Inspired by https://github.com/plone/plone.formwidget.autocomplete/issues/15
        Return the current request user based on cookie credentials"""
        if api.user.is_anonymous():
            portal = api.portal.get()
            app = portal.__parent__
            request = portal.REQUEST
            creds = portal.acl_users.credentials_cookie_auth.extractCredentials(request)
            user = None
            if "login" in creds and creds["login"]:
                # first try the portal (non-admin accounts)
                user = portal.acl_users.authenticate(creds["login"], creds["password"], request)
                if not user:
                    # now try the app (i.e. the admin account)
                    user = app.acl_users.authenticate(creds["login"], creds["password"], request)
            return user
        else:
            return api.user.get_current()

    @property
    def vocabulary(self):
        if not self._vocabulary:
            current_user = self._verified_user
            if current_user:
                with api.env.adopt_user(user=current_user):
                    self._vocabulary = classification_tree_vocabulary_factory(self.context)
            else:
                self._vocabulary = SimpleVocabulary([])
        return self._vocabulary

    def getTerm(self, value):
        try:
            return self.vocabulary.getTerm(value)
        except LookupError:
            # all form widgets are called when using plone.formwidget.masterselect on a form field
            # this is done as anonymous and the vocabulary is then empty
            # it's not necessary here to render the correct term
            # see z3c.form.term
            if "++widget++" in self.context.REQUEST.get("URL", ""):
                return SimpleTerm(
                    value,
                    util.createCSSId(util.toUnicode(value)),
                    title=_zf(u"Missing: ${value}", mapping=dict(value=util.toUnicode(value))),
                )
            raise

    def getTermByToken(self, value):
        return self.vocabulary.getTermByToken(value)

    def search(self, query_string):
        q_parts = unidecode(query_string).lower().split()
        results = []
        for term in self.vocabulary:
            if self.enabled is not None and term.attrs.get("enabled") != self.enabled:
                continue
            if all([q in unidecode(term.title).lower() for q in q_parts]):
                results.append(term)
            if len(results) >= 10:
                break
        return results


@implementer(IContextSourceBinder)
class ClassificationTreeSourceBinder(object):
    def __init__(self, enabled=None):
        self.enabled = enabled  # None for all or True or False

    def __call__(self, context):
        return ClassificationTreeSource(context, self.enabled)
