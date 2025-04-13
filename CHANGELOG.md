# CHANGELOG

<!--next-version-placeholder-->

## [2025.04.13.1]

### Code Refactoring
- Remove print stmt, move commented code (tidy) [#255](https://github.com/imAsparky/django-tag-me/pull/255)


## [2025.02.20.1]

### Documentation
- Update settings names after refactor (settings) [#253](https://github.com/imAsparky/django-tag-me/pull/253)

### Code Refactoring
- Updating settings names and tag parsing (general) [#253](https://github.com/imAsparky/django-tag-me/pull/253)

### Testing
- Update for settings name changes (refactor) [#253](https://github.com/imAsparky/django-tag-me/pull/253)


## [2025.02.18.1]

### Documentation
- Add AllFieldTagMeMixin (quickstart) [#248](https://github.com/imAsparky/django-tag-me/pull/248)

### Features
- Add tags to the AllFields mixin (system) [#248](https://github.com/imAsparky/django-tag-me/pull/248)

### Bug Fixes
- Add css class for height and width (templatetag) [#251](https://github.com/imAsparky/django-tag-me/pull/251)

### Code Refactoring
- Delete redundant commands (commands) [#248](https://github.com/imAsparky/django-tag-me/pull/248)
- Remove print debug (print) [#248](https://github.com/imAsparky/django-tag-me/pull/248)
- Update for tag management refactor (tags) [#248](https://github.com/imAsparky/django-tag-me/pull/248)

### Testing
- Update all tests for new tag management (tags) [#248](https://github.com/imAsparky/django-tag-me/pull/248)


## [2025.02.11.1]

### Features
- Add All user tag fields generated for search tools (mixin) [#246](https://github.com/imAsparky/django-tag-me/pull/246)
- Add attr for adding all tags to selection (tags) [#247](https://github.com/imAsparky/django-tag-me/pull/247)

### Bug Fixes
- Remove class dropping select menu (html) [#245](https://github.com/imAsparky/django-tag-me/pull/245)

### Testing
- Add mixin, update widget tests (mixin) [#246](https://github.com/imAsparky/django-tag-me/pull/246)


## [2025.02.04.1]

### Maintenance
- Add empty string for option 0 (select) [#242](https://github.com/imAsparky/django-tag-me/pull/242)

### Testing
- Add test suite (widget) [#242](https://github.com/imAsparky/django-tag-me/pull/242)
- Override fails to get update merged (gha) [#242](https://github.com/imAsparky/django-tag-me/pull/242)
  > The tests pass locally.
New issue to follow up #244


## [2025.01.27.1]

### ⚠ BREAKING CHANGES
- BREAKING: Simplify TagMeCharfield names (attrs) [#239](https://github.com/imAsparky/django-tag-me/pull/239)
  > Update attr name to `multiple` , previous was to verbose and
not aligned with common naming conventions in templates.

### Maintenance
- BREAKING: Simplify TagMeCharfield names (attrs) [#239](https://github.com/imAsparky/django-tag-me/pull/239)
  > Update attr name to `multiple` , previous was to verbose and
not aligned with common naming conventions in templates.

### Documentation
- Add templatetag usage (quickstart) [#239](https://github.com/imAsparky/django-tag-me/pull/239)

### Testing
- Update versions matrix (tox) [#240](https://github.com/imAsparky/django-tag-me/pull/240)


## [2025.01.25.2]

### Maintenance
- Add non signing for changelog fork PR (workflow) [#234](https://github.com/imAsparky/django-tag-me/pull/234)


## [2025.01.25.1]

### Maintenance
- Update mainPR for fork PR (workflow) [#232](https://github.com/imAsparky/django-tag-me/pull/232)


## [2025.01.24.1]

### Maintenance
- Update items to match contributing guide (example) [#227](https://github.com/imAsparky/django-tag-me/pull/227)

### Bug Fixes
- Update errors in setup process for dev (docs) [#227](https://github.com/imAsparky/django-tag-me/pull/227)
  > Several steps had incorrect info, not updated as changes
in the project progressed.


## [2025.01.23.1]

### Bug Fixes
- Add alpine bind for multiselect (multi) [#225](https://github.com/imAsparky/django-tag-me/pull/225)


## [2025.01.18.1]

### Bug Fixes
- Upload to Pypi error logging (git) [#222](https://github.com/imAsparky/django-tag-me/pull/222)


## [2025.01.17.2]

### Bug Fixes
- Add logging for debug (git) [#213](https://github.com/imAsparky/django-tag-me/pull/213)


## [2025.01.17.1]

### Documentation
- Add settings and `TagMeCharfield` examples (config) [#218](https://github.com/imAsparky/django-tag-me/pull/218)

### Features
- Field choices accepts a list (field) [#218](https://github.com/imAsparky/django-tag-me/pull/218)

### Bug Fixes
- Fix occasional text hidden by colour (css) [#218](https://github.com/imAsparky/django-tag-me/pull/218)

### Testing
- Add test for choices list option (field) [#218](https://github.com/imAsparky/django-tag-me/pull/218)


## [2024.12.18.1]

### Maintenance
- Fine tune the deploy steps (git) [#213](https://github.com/imAsparky/django-tag-me/pull/213)


## [2024.12.17.1]

### Maintenance
- Improve build process (build) [#210](https://github.com/imAsparky/django-tag-me/pull/210)


## [2024.12.16.6]

### Bug Fixes
- Add handling of `Postgres ProgrammingError` (migrations) [#208](https://github.com/imAsparky/django-tag-me/pull/208)


## [2024.12.16.5]

### Maintenance
- Add link to readme docs (docs) [#206](https://github.com/imAsparky/django-tag-me/pull/206)


## [2024.12.16.4]

### Maintenance
- Update version to the new date format (docs) [#204](https://github.com/imAsparky/django-tag-me/pull/204)


## [2024.12.16.3]

### Bug Fixes
- Removed erroneous license reference (build) [#202](https://github.com/imAsparky/django-tag-me/pull/202)


## [2024.12.16.2]

### Maintenance
- Remove use of semantic release (version) [#200](https://github.com/imAsparky/django-tag-me/pull/200)
  > Using GHA python script to handle versioning and changelog updates.

### Documentation
- Fix format so pypi displays correctly (pypi) [#200](https://github.com/imAsparky/django-tag-me/pull/200)


## [2024.12.16.1]

### Maintenance
- Add select deploy and deploy to pypi (git) [#198](https://github.com/imAsparky/django-tag-me/pull/198)


## [2024.12.15.2]

### Maintenance
- Add logging and user feedback for test upload (git) [#196](https://github.com/imAsparky/django-tag-me/pull/196)

### Formatting, missing semi colons, etc; no code change
- General tidy up of workflows (git) [#196](https://github.com/imAsparky/django-tag-me/pull/196)


## [2024.12.15.1]

### Maintenance
- Add deploy to test pypi (git) [#194](https://github.com/imAsparky/django-tag-me/pull/194)

### Documentation
- Fixed typo in line spacings (README) [#194](https://github.com/imAsparky/django-tag-me/pull/194)


## [2024.12.14.1]

### Maintenance
- Add package file version updating (git) [#192](https://github.com/imAsparky/django-tag-me/pull/192)
- Add release/deploy workflow (git) [#192](https://github.com/imAsparky/django-tag-me/pull/192)

### Bug Fixes
- Syntax error, empty env, add files to message (git) [#192](https://github.com/imAsparky/django-tag-me/pull/192)

### Code Refactoring
- Remove PR used for testing (git) [#192](https://github.com/imAsparky/django-tag-me/pull/192)
- Update branch message references (git) [#192](https://github.com/imAsparky/django-tag-me/pull/192)

### Testing
- Update test env for GHA runs/testing (tox) [#192](https://github.com/imAsparky/django-tag-me/pull/192)


