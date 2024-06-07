# -*- coding: utf-8 -*-

from BTrees.OOBTree import OOBTree
from OFS.event import ObjectWillBeRemovedEvent
from collective.classification.tree import caching
from collective.classification.tree.contents.common import BaseContainer
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.container.contained import ContainerModifiedEvent
from zope.event import notify
from zope.interface import implementer
from zope.lifecycleevent import ObjectRemovedEvent

import six


class IClassificationContainer(model.Schema):
    pass


@implementer(IClassificationContainer)
class ClassificationContainer(Container, BaseContainer):
    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, *args, **kwargs):
        self._tree = OOBTree()
        super(ClassificationContainer, self).__init__(*args, **kwargs)

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
        return [
            (
                i[0],
                i[1].__of__(self),
            )
            for i in self._tree.items()
        ]

    def values(self):
        return [v.__of__(self) for v in self._tree.values()]

    def iterkeys(self):
        return six.iterkeys(self._tree)

    def itervalues(self):
        for v in six.itervalues(self._tree):
            yield v.__of__(self)

    def iteritems(self):
        for k, v in six.iteritems(self._tree):
            yield (
                k,
                v.__of__(self),
            )

    def allowedContentTypes(self):
        return []


def container_modified(context, event):
    """Invalidates tree cache node."""
    caching.invalidate_cache("collective.classification.tree.utils.iterate_over_tree", context.UID())
