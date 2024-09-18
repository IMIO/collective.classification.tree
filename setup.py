# -*- coding: utf-8 -*-
"""Installer for the collective.classification.tree package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="collective.classification.tree",
    version="1.1.1",
    description="Addon to manage complex content classification tree",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="Martin Peeters",
    author_email="support@imio.be",
    url="https://github.com/imio/collective.classification.tree",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/collective.classification.tree",
        "Source": "https://github.com/imio/collective.classification.tree",
        "Tracker": "https://github.com/imio/collective.classification.tree/issues",
        # 'Documentation': 'https://collective.classification.tree.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["collective", "collective.classification"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "z3c.jbot",
        "Products.GenericSetup>=1.8.2",
        "plone.api>=1.8.4",
        "plone.restapi",
        "plone.app.dexterity",
        "plone.app.referenceablebehavior",
        "plone.app.relationfield",
        "plone.app.lockingbehavior",
        "plone.schema",
        "collective.js.datatables",
        "imio.helpers>=1.0.0rc4",
        "imio.pyutils",
        "Unidecode",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing",
            "plone.app.robotframework[debug]",
            "plone.app.contenttypes",
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = collective.classification.tree.locales.update:update_locale
    tree_compare_files = collective.classification.tree.script:compare_tree_files
    tree_add_parent = collective.classification.tree.script:add_parent
    tree_add_archived = collective.classification.tree.script:add_archived
    """,
)
