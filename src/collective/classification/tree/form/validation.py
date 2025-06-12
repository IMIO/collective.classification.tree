# -*- coding: utf-8 -*-

from plone.app.z3cform.inline_validation import InlineValidationView

import json


class InlineValidationView(InlineValidationView):
    """Validate a form and return the error message for a particular field as JSON."""

    def __call__(self, fname=None, fset=None):
        self.request.response.setHeader("Content-Type", "application/json")
        res = {"errmsg": ""}
        return json.dumps(res)
