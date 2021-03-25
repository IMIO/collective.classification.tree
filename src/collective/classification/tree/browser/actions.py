# -*- coding: utf-8 -*-

from plone.app.contentmenu.menu import ActionsSubMenuItem as BaseActionsSubMenuItem
from plone.app.layout.globals.context import ContextState as BaseContextState


class ContextState(BaseContextState):
    def actions(self, category, **kwargs):
        base_actions = super(ContextState, self).actions(category, **kwargs)
        if category in ("user", "portal_tabs", "site_actions"):
            return base_actions
        elif category == "object":
            return [
                {
                    "available": True,
                    "category": "object",
                    "description": "",
                    "icon": "",
                    "title": "View",
                    "url": "{0}/view".format(self.context.absolute_url()),
                    "visible": True,
                    "allowed": True,
                    "link_target": None,
                    "id": "view",
                },
                {
                    "available": True,
                    "category": "object",
                    "description": "",
                    "icon": "",
                    "title": "Edit",
                    "url": "{0}/edit".format(self.context.absolute_url()),
                    "visible": True,
                    "allowed": True,
                    "link_target": None,
                    "id": "edit",
                },
            ]
        else:
            return []

    def _lookupTypeActionTemplate(self, actionId):
        return None


class ActionsSubMenuItem(BaseActionsSubMenuItem):
    def available(self):
        return False
