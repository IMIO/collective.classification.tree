from App.class_init import InitializeClass
from collective.classification.tree import SOURCE_RESULTS_LEN
from plone.formwidget.autocomplete.interfaces import IAutocompleteWidget
from plone.formwidget.autocomplete.widget import AutocompleteBase as OriginalAutocompleteBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.formwidget.query.widget import QuerySourceCheckboxWidget
from zope.interface import implementer
from zope.interface import implementer_only

import os
import plone.formwidget.autocomplete
import z3c.form.interfaces
import z3c.form.util
import z3c.form.widget


pfa_path = os.path.dirname(plone.formwidget.autocomplete.__file__)


@implementer_only(IAutocompleteWidget)
class AutocompleteBase(OriginalAutocompleteBase):

    maxResults = SOURCE_RESULTS_LEN

    # JavaScript template
    js_template = """\
    (function($) {
        $().ready(function() {
            $('#%(id)s-input-fields').data('klass','%(klass)s').data('title','%(title)s').data('input_type',
                                      '%(input_type)s').data('multiple', %(multiple)s);
            $('#%(id)s-buttons-search').remove();
            $('#%(id)s-widgets-query').autocomplete('%(url)s', {
                autoFill: %(autoFill)s,
                minChars: %(minChars)d,
                max: %(maxResults)d,
                mustMatch: %(mustMatch)s,
                matchContains: %(matchContains)s,
                formatItem: %(formatItem)s,
                formatResult: %(formatResult)s,
                parse: %(parseFunction)s
            }).result(%(js_callback)s);
            %(js_extra)s
        });
    })(jQuery);
    """


InitializeClass(AutocompleteBase)


class AutocompleteMultiSelectionWidget(AutocompleteBase, QuerySourceCheckboxWidget):
    """Autocomplete widget for multiple selection."""

    klass = u'autocomplete-multiselection-widget'
    input_type = 'checkbox'
    multiple = True
    display_template = ViewPageTemplateFile('display.pt', _prefix=pfa_path)


@implementer(z3c.form.interfaces.IFieldWidget)
def AutocompleteMultiFieldWidget(field, request):
    return z3c.form.widget.FieldWidget(field, AutocompleteMultiSelectionWidget(request))
