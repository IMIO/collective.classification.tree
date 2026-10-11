# -*- coding: utf-8 -*-

from collective.classification.tree import testing
from plone import api

import json
import unittest


class TestInlineValidationView(unittest.TestCase):
    layer = testing.COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING

    def test___call__(self):
        container = api.content.create(
            title="Container",
            type="ClassificationContainer",
            container=self.layer["portal"],
        )
        request = self.layer["request"]
        request.form = {"fname": "form.widgets.source"}
        for name in ("@@import", "@@import-process"):
            # no inline validation on the import forms (the file is not posted)
            result = container.restrictedTraverse(name + "/@@z3cform_validate_field")()
            self.assertEqual({"errmsg": ""}, json.loads(result))
            self.assertEqual(
                "application/json", request.response.getHeader("Content-Type")
            )
