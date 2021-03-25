# -*- coding: utf-8 -*-

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.testing import z2
from plone.app.testing import setRoles

import collective.classification.tree


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
        applyProfile(portal, "collective.classification.tree:default")
        setRoles(portal, TEST_USER_ID, ["Manager"])


COLLECTIVE_CLASSIFICATION_TREE_FIXTURE = CollectiveClassificationTreeLayer()


COLLECTIVE_CLASSIFICATION_TREE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_CLASSIFICATION_TREE_FIXTURE,),
    name="CollectiveClassificationTreeLayer:IntegrationTesting",
)


COLLECTIVE_CLASSIFICATION_TREE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_CLASSIFICATION_TREE_FIXTURE,),
    name="CollectiveClassificationTreeLayer:FunctionalTesting",
)


COLLECTIVE_CLASSIFICATION_TREE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_CLASSIFICATION_TREE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="CollectiveClassificationTreeLayer:AcceptanceTesting",
)
