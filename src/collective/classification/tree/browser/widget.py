# -*- coding: utf-8 -*-

from plone.app.z3cform.widgets.select import AjaxSelectWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from zope.interface import implementer


class SourceAjaxSelectWidget(AjaxSelectWidget):
    """Select2 widget on a source, showing term titles (not tokens) as values"""

    def get_vocabulary(self):
        # plone.app.z3cform only looks up named vocabularies
        if getattr(self, "_source", None) is None:
            self._source = self.field.bind(self.context).value_type.vocabulary
        return self._source

    def get_pattern_options(self):
        options = super().get_pattern_options()
        if self.value:
            vocabulary = self.get_vocabulary()
            options["initialValues"] = {}
            for token in self.value.split(self.separator):
                try:
                    title = vocabulary.getTermByToken(token).title
                except LookupError:
                    title = token
                options["initialValues"][token] = title
        return options


@implementer(IFieldWidget)
def SourceAjaxSelectFieldWidget(field, request):
    return FieldWidget(field, SourceAjaxSelectWidget(request))
