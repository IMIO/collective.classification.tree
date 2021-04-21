# -*- coding: utf-8 -*-

from Acquisition import Implicit
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from OFS.Traversable import Traversable
from OFS.event import ObjectWillBeRemovedEvent
from Products.CMFCore.DynamicType import DynamicType
from collective.classification.tree import _
from collective.classification.tree import caching
from collective.classification.tree import utils
from collective.classification.tree.contents.common import BaseContainer
from persistent import Persistent
from plone.dexterity.fti import DexterityFTI
from plone.rest.interfaces import IService
from plone.uuid.interfaces import IAttributeUUID
from plone.uuid.interfaces import IMutableUUID
from zope import schema
from zope.component.factory import Factory
from zope.container.contained import ContainerModifiedEvent
from zope.event import notify
from zope.interface import Interface
from zope.interface import implementer
from zope.lifecycleevent import ObjectRemovedEvent
from zope.schema.fieldproperty import FieldProperty

import six


class IClassificationCategory(Interface):
    identifier = schema.TextLine(
        title=_(u"Identifier"),
        description=_("Identifier of the category"),
        required=True,
    )

    title = schema.TextLine(
        title=_(u"Name"), description=_("Name of the category"), required=True
    )

    informations = schema.TextLine(title=_(u"Informations"), required=False)


@implementer(IClassificationCategory, IAttributeUUID, IService)
class ClassificationCategory(
    DynamicType, Traversable, Implicit, Persistent, BaseContainer
):
    __parent__ = None
    __allow_access_to_unprotected_subobjects__ = True
    portal_type = "ClassificationCategory"

    identifier = FieldProperty(IClassificationCategory["identifier"])
    title = FieldProperty(IClassificationCategory["title"])
    informations = FieldProperty(IClassificationCategory["informations"])

    def __init__(self, *args, **kwargs):
        self._tree = OOBTree()
        super(ClassificationCategory, self).__init__(*args, **kwargs)

    def getId(self):
        return self.UID()

    def Title(self):
        return u"{0} - {1}".format(self.identifier, self.title)

    def UID(self):
        return IMutableUUID(self).get()

    def __len__(self):
        return len(self._tree)

    def __contains__(self, key):
        return key in self._tree

    def __getitem__(self, key):
        return self._tree[key].__of__(self)

    def __delitem__(self, key, suppress_container_modified=False):
        element = self[key].__of__(self)
        notify(ObjectWillBeRemovedEvent(element, self, key))

        # Remove the element from _tree
        self._tree.pop(key)
        notify(ObjectRemovedEvent(element, self, key))
        if not suppress_container_modified:
            notify(ContainerModifiedEvent(self))

    def __iter__(self):
        return iter(self._tree)

    def get(self, key, default=None):
        element = self._tree.get(key, default)
        if element is default:
            return default
        return element.__of__(self)

    def keys(self):
        return self._tree.keys()

    def items(self):
        return [(i[0], i[1].__of__(self)) for i in self._tree.items()]

    def values(self):
        return [v.__of__(self) for v in self._tree.values()]

    def iterkeys(self):
        return six.iterkeys(self._tree)

    def itervalues(self):
        for v in six.itervalues(self._tree):
            yield v.__of__(self)

    def iteritems(self):
        for k, v in six.iteritems(self._tree):
            yield (k, v.__of__(self))

    def allowedContentTypes(self):
        return []

    def getTypeInfo(self):
        fti = DexterityFTI("ClassificationCategory")
        return fti

    def manage_delObjects(self, ids=None, REQUEST=None):
        """Delete the contained objects with the specified ids"""
        if ids is None:
            ids = []
        if isinstance(ids, basestring):
            ids = [ids]
        for id in ids:
            del self[id]


ClassificationCategoryFactory = Factory(ClassificationCategory)


def container_modified(context, event):
    func = "collective.classification.tree.utils.iterate_over_tree"
    for element in utils.get_chain(context):
        caching.invalidate_cache(func, element.UID())


def category_modified(context, event):
    # This allow cache invalidation on edit
    notify(ContainerModifiedEvent(aq_parent(context)))
