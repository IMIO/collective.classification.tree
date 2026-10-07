# -*- coding: utf-8 -*-

from plone import api
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.fti import DexterityFTI

import collective.classification.tree
import unittest


try:  # Plone 5.2+
    from plone.testing.zope import Browser  # noqa: F401
    from plone.testing.zope import WSGI_SERVER_FIXTURE as SERVER_FIXTURE
except ImportError:  # Plone 4.3
    from plone.testing.z2 import Browser  # noqa: F401
    from plone.testing.z2 import ZSERVER_FIXTURE as SERVER_FIXTURE


PLONE_VERSION = api.env.plone_version()[:3]
PLONE_MAJOR = int(PLONE_VERSION.split(".")[0])
BEHAVIOR = "collective.classification.tree.behaviors.classification.IClassificationCategory"


def plone6_bug(test):
    """Expected failure on Plone 6: Plone 4 behaviour lost by the migration (fixed in phase 7)"""
    return unittest.expectedFailure(test) if PLONE_MAJOR >= 6 else test


def plone4_bug(test):
    """Expected failure on Plone 4: bug of the Plone 4 release, fixed on the Plone 6 branch"""
    return unittest.expectedFailure(test) if PLONE_MAJOR < 5 else test


def new_request(request, form=None):
    """Reuse the test request as a new browser request: GET, or POST of the form values.
    Plone 4 copies the submitted values in request.other, read first by request.get"""
    for key in [k for k in request.other if k.startswith("form.")]:
        del request.other[key]
    request["REQUEST_METHOD"] = form and "POST" or "GET"
    request.form = form or {}
    request.response.setStatus(200)


class CollectiveClassificationTreeLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.classification.tree)

    def setUpPloneSite(self, portal):
        # installed with the add-on in the sites (the listing uses @tree): "Use REST API" for Anonymous
        applyProfile(portal, "plone.restapi:default")
        applyProfile(portal, "collective.classification.tree:default")
        setRoles(portal, TEST_USER_ID, ["Manager"])
        # a content type classified with the behavior, as the mails of imio.dms.mail
        fti = DexterityFTI("ClassifiedItem", klass="plone.dexterity.content.Item", global_allow=True)
        fti.behaviors = (BEHAVIOR,)
        portal.portal_types._setObject("ClassifiedItem", fti)


COLLECTIVE_CLASSIFICATION_TREE_FIXTURE = CollectiveClassificationTreeLayer()


COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_CLASSIFICATION_TREE_FIXTURE,),
    name="CollectiveClassificationTreeLayer:IntegrationTesting",
)


COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_CLASSIFICATION_TREE_FIXTURE,),
    name="CollectiveClassificationTreeLayer:FunctionalTesting",
)


ACCEPTANCE = FunctionalTesting(
    bases=(
        COLLECTIVE_CLASSIFICATION_TREE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        SERVER_FIXTURE,
    ),
    name="CollectiveClassificationTreeLayer:AcceptanceTesting",
)
COLLECTIVE_CLASSIFICATION_TREE_ACCEPTANCE_TESTING = ACCEPTANCE  # former name
