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

    def _add_element(self, element):
        element = aq_base(element)
        uid = self._generate_uid()
        IMutableUUID(element).set(uid)

        notify(ObjectWillBeAddedEvent(element, self, uid))
        self._tree[uid] = element
        element.__parent__ = aq_base(self)

        notify(ObjectCreatedEvent(element))
        notify(ObjectAddedEvent(element.__of__(self), self, uid))
        notify(ContainerModifiedEvent(self))

    def _update_element(self, element):
        element = aq_base(element)
        self._tree[element.UID()] = element
        notify(ObjectModifiedEvent(element))

    def _delete_element(self, element):
        uid = element.UID()
        notify(ObjectWillBeRemovedEvent(element, self, uid))
        del self._tree[uid]
        notify(ObjectRemovedEvent(element, self, uid))
        notify(ContainerModifiedEvent(self))
