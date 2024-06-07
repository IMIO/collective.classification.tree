# -*- coding: utf-8 -*-

from collective.classification.tree import _
from collective.classification.tree.contents.category import IClassificationCategory
from plone.restapi.interfaces import ISerializeToJson
from plone import api
from zope.component import adapter
from zope.i18n import translate
from zope.interface import Interface
from zope.interface import implementer


@implementer(ISerializeToJson)
@adapter(IClassificationCategory, Interface)
class SerializeToJson(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        obj = self.context
        result = {
            "@id": obj.absolute_url(),
            "UID": obj.UID(),
            "identifier": obj.identifier,
            "title": obj.title,
            "informations": obj.informations,
            "enabled": obj.enabled
            and translate(_("Yes"), context=self.request)
            or translate(_("No"), context=self.request),
            "links": self._links,
        }

        return result

    @property
    def _links(self):
        if not api.user.has_permission("cmf.ModifyPortalContent"):
            return []
        return [
            {
                "title": translate(_("Edit"), context=self.request),
                "link": "{0}/edit".format(self.context.absolute_url()),
            },
            {
                "title": translate(_("Add"), context=self.request),
                "link": "{0}/add-{1}".format(self.context.absolute_url(), self.context.portal_type),
            },
        ]
