# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from collective.classification.tree import utils
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.layout.globals.context import ContextState as BaseContextState
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter


class ContextState(BaseContextState):
    def actions(self, category, **kwargs):
        base_actions = super(ContextState, self).actions(category, **kwargs)
        if category in ("user", "portal_tabs", "site_actions"):
            return base_actions
        elif category == "object_buttons":
            actions = [a for a in base_actions if a["id"] in ("delete")]
            return actions
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

    def is_structural_folder(self):
        return True

    def is_default_page(self):
        """Override since default view is a listing view"""
        return False


class LockingBase(BrowserView):
    @property
    def is_locked(self):
        locking_view = queryMultiAdapter((self.context, self.request), name="plone_lock_info")

        return locking_view and locking_view.is_locked_for_current_user()


class DeleteConfirmationForm(form.Form, LockingBase):
    """Inspired by view from plone.app.content latest versions"""

    fields = field.Fields()
    template = ViewPageTemplateFile("templates/delete_confirmation.pt")
    enableCSRFProtection = True

    def view_url(self):
        """Facade to the homonymous plone_context_state method"""
        context_state = getMultiAdapter((self.context, self.request), name="plone_context_state")
        return context_state.view_url()

    def more_info(self):
        adapter = queryMultiAdapter((self.context, self.request), name="delete_confirmation_info")
        if adapter:
            return adapter()
        return ""

    @property
    def items_to_delete(self):
        return len(utils.iterate_over_tree(self.context))

    @button.buttonAndHandler(_(u"Delete"), name="Delete")
    def handle_delete(self, action):
        title = safe_unicode(self.context.Title())
        parent = aq_parent(aq_inner(self.context))

        # has the context object been acquired from a place it should not have
        # been?
        if self.context.aq_chain == self.context.aq_inner.aq_chain:
            parent.manage_delObjects(self.context.getId())
            IStatusMessage(self.request).add(_(u"${title} has been deleted.", mapping={u"title": title}))
        else:
            IStatusMessage(self.request).add(_(u'"${title}" has already been deleted', mapping={u"title": title}))

        self.request.response.redirect(parent.absolute_url())

    @button.buttonAndHandler(_(u"label_cancel", default=u"Cancel"), name="Cancel")
    def handle_cancel(self, action):
        target = self.view_url()
        return self.request.response.redirect(target)
