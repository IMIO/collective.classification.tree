Changelog
=========


2.0.0 (unreleased)
------------------

- Migrated to Plone 6.2 / Python 3, based on the work started by @sgeulette,
  @mpeeters and @anuyens on `plone6`.
  [sgeulette, mpeeters, anuyens, chris-adam]
- Made compatible Plone 4.3 and Plone 6.0
  [sgeulette]
- Added Plone 6.2 support, dropped Plone 4.
  Fixed `default_identifier` recursion, `@tree` ordering with empty values,
  `tree_add_parent` and `tree_add_archived` on Python 3,
  serializer links permission (listing for non-Managers).
  [chris-adam]
- Fixed the categories widget showing UIDs instead of titles (`SourceAjaxSelectFieldWidget`).
  [chris-adam]
- Fixed `ClassificationTreeSource` for a user missing from the user folders (MemberData error).
  [chris-adam]

1.3.0 (2026-08-14)
------------------

- Fixed `ConnectionStateError` in `iterate_over_tree`.
  [chris-adam]


1.2.0 (2024-12-13)
------------------

- Improved `vocabularies.ClassificationTreeSource.search` to order results search by matching positions.
  [sgeulette]

1.1.1 (2024-09-18)
------------------

- Don't create wheel.
  [sgeulette]

1.1.0 (2024-09-17)
------------------

- Added classification_category indexer to store empty value.
  [sgeulette]

1.0.1 (2024-06-07)
------------------

- Defined category identifier defaut value based on parent.
  [sgeulette]
- Blacked files
  [sgeulette]

1.0.0 (2024-03-01)
------------------

- Handled `bool` on category object.
  [sgeulette]

1.0a3 (2023-09-08)
------------------

- Removed python_requires causing problem to download from pypi
  [sgeulette]

1.0a2 (2023-07-20)
------------------

- Corrected setup urls.
  [sgeulette]

1.0a1 (2023-03-29)
------------------

- Initial release.
  [mpeeters]
