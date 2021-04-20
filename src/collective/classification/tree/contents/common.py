# -*- coding: utf-8 -*-

from Acquisition import aq_base
from OFS.event import ObjectWillBeAddedEvent
from OFS.event import ObjectWillBeRemovedEvent
from plone.uuid.interfaces import IMutableUUID
from plone.uuid.interfaces import IUUIDGenerator
from zope.component import queryUtility
from zope.container.contained import ContainerModifiedEvent
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectRemovedEvent


class BaseContainer(object):
    """Mixin class for category tree container"""

    def _generate_uid(self):
        generator = queryUtility(IUUIDGenerator)
        if generator is None:
            return

        uuid = generator()
        if not uuid:
            return
        return uuid

    def _add_element(self, element, event=True):
        element = aq_base(element)
        uid = self._generate_uid()
        IMutableUUID(element).set(uid)

        if event is True:
            notify(ObjectWillBeAddedEvent(element, self, uid))
        self._tree[uid] = element
        element.__parent__ = aq_base(self)

        if event is True:
            notify(ObjectCreatedEvent(element))
            notify(ObjectAddedEvent(element.__of__(self), self, uid))
            notify(ContainerModifiedEvent(self))

    def _update_element(self, element, event=True):
        element = aq_base(element)
        self._tree[element.UID()] = element
        if event is True:
            notify(ObjectModifiedEvent(element))

    def _delete_element(self, element, event=True):
        uid = element.UID()
        if event is True:
            notify(ObjectWillBeRemovedEvent(element, self, uid))

        del self._tree[uid]
        if event is True:
            notify(ObjectRemovedEvent(element, self, uid))
            notify(ContainerModifiedEvent(self))

    def get_by(self, identifier, key):
        filtered = [e for e in self.values() if getattr(e, identifier) == key]
        if len(filtered) > 0:
            return filtered[0]
