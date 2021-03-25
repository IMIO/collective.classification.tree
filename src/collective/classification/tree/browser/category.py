# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.classification.tree import _
from collective.classification.tree.contents.category import IClassificationCategory
from plone import api
from plone.autoform.form import AutoExtensibleForm
from plone.autoform.view import WidgetsView
from plone.z3cform.layout import FormWrapper
from z3c.form import button
from z3c.form.form import AddForm
from z3c.form.form import EditForm
from zope.component import createObject


class CategoryView(WidgetsView):
    schema = IClassificationCategory


class CategoryEditForm(AutoExtensibleForm, EditForm):
    schema = IClassificationCategory

    @property
    def label(self):
        return _("Edit Classification Category")

    def update_element(self, data):
        element = self.context
        for key, value in data.items():
            setattr(element, key, value)
        aq_parent(self.context)._update_element(element)
        api.portal.show_message(_(u"Changes saved"), request=self.request)
        self.request.response.redirect(self.redirect_url)

    @property
    def redirect_url(self):
        return self.context.absolute_url()

    @button.buttonAndHandler(_(u"Save"), name="save")
    def handle_save(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        self.update_element(data)

    @button.buttonAndHandler(_(u"Cancel"), name="cancel")
    def handle_cancel(self, action):
        self.request.response.redirect(self.redirect_url)


class CategoryEditView(FormWrapper):
    form = CategoryEditForm


class CategoryAddForm(AutoExtensibleForm, AddForm):
    schema = IClassificationCategory
    ignoreContext = True

    @property
    def label(self):
        return _("Add Classification Category")

    def add_element(self, data):
        element = createObject("ClassificationCategory")
        for key, value in data.items():
            setattr(element, key, value)
        self.context._add_element(element)
        api.portal.show_message(_(u"Category added"), request=self.request)
        url = "{0}/view".format(element.absolute_url())
        self.request.response.redirect(url)

    @button.buttonAndHandler(_(u"Add"), name="add")
    def handle_add(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        self.add_element(data)

    @button.buttonAndHandler(_(u"Cancel"), name="cancel")
    def handle_cancel(self, action):
        self.request.response.redirect(self.context.absolute_url())


class CategoryAddView(FormWrapper):
    form = CategoryAddForm
