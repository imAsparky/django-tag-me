# CHANGELOG

<!--next-version-placeholder-->

## [2026.02.26.2]

### Maintenance
- Delete unused files (housekeeping) [#334](https://github.com/imAsparky/django-tag-me/pull/334)
- Update dependencies (frontend) [#336](https://github.com/imAsparky/django-tag-me/pull/336)


## [2026.02.26.1]

### Documentation
- Update management command changes (mgmt) [#332](https://github.com/imAsparky/django-tag-me/pull/332)

### Bug Fixes
- Takes contentype.cache into account for migrations (mgmt) [#332](https://github.com/imAsparky/django-tag-me/pull/332)

### Testing
- Refactor/Add tests for new mgmt command (all) [#332](https://github.com/imAsparky/django-tag-me/pull/332)


## [2026.02.24.1]

### Bug Fixes
- Multiple select option working (select) [#330](https://github.com/imAsparky/django-tag-me/pull/330)


## [2026.02.21.2]

### Maintenance
- Update for deploy (assets) [#328](https://github.com/imAsparky/django-tag-me/pull/328)

### Documentation
- Update style usage (quickstart) [#328](https://github.com/imAsparky/django-tag-me/pull/328)

### Bug Fixes
- Add correct MD3 to style and template rings (style) [#328](https://github.com/imAsparky/django-tag-me/pull/328)


## [2026.02.21.1]

### Maintenance
- Update for deploy (assets) [#326](https://github.com/imAsparky/django-tag-me/pull/326)

### Documentation
- Add template min-height usage (quickstart) [#326](https://github.com/imAsparky/django-tag-me/pull/326)

### Features
- Add tm-input-height for finer control (style) [#326](https://github.com/imAsparky/django-tag-me/pull/326)


## [2026.02.17.1]

### Maintenance
- Update deps (frontend) [#324](https://github.com/imAsparky/django-tag-me/pull/324)
- Update for deploy (assets) [#324](https://github.com/imAsparky/django-tag-me/pull/324)

### Documentation
- Add django form-save integration (quickstart) [#324](https://github.com/imAsparky/django-tag-me/pull/324)

### Features
- Add django form draft save integration (frontend) [#324](https://github.com/imAsparky/django-tag-me/pull/324)

### Testing
- Add latest python/django versions to matrix (tox) [#324](https://github.com/imAsparky/django-tag-me/pull/324)


## [2026.01.07.1]

### Bug Fixes
- Replace RunPython with AddConstraint (migration) [#322](https://github.com/imAsparky/django-tag-me/pull/322)


## [2026.01.05.1]

### ⚠ BREAKING CHANGES
- BREAKING: Add FK-based lookups for model rename resilience (migration) [#320](https://github.com/imAsparky/django-tag-me/pull/320)

### Maintenance
- Add migrations for updated models (migrations) [#320](https://github.com/imAsparky/django-tag-me/pull/320)
- Update versions and status (pyproject) [#320](https://github.com/imAsparky/django-tag-me/pull/320)

### Documentation
- Add info for fk lookup based system (how-to) [#320](https://github.com/imAsparky/django-tag-me/pull/320)
- Update with new info (README) [#320](https://github.com/imAsparky/django-tag-me/pull/320)

### Features
- BREAKING: Add FK-based lookups for model rename resilience (migration) [#320](https://github.com/imAsparky/django-tag-me/pull/320)

### Code Refactoring
- Add command to python path (management) [#320](https://github.com/imAsparky/django-tag-me/pull/320)

### Testing
- Add model rename handling tests (migrations) [#320](https://github.com/imAsparky/django-tag-me/pull/320)


## [2025.12.11.2]

### Bug Fixes
- Remove call to super.render(), not needed (widget) [#317](https://github.com/imAsparky/django-tag-me/pull/317)

### Testing
- Add optgroup testing (widget) [#317](https://github.com/imAsparky/django-tag-me/pull/317)


## [2025.12.11.1]

### Documentation
- Add widget standalone usage (howto) [#315](https://github.com/imAsparky/django-tag-me/pull/315)

### Code Refactoring
- Simplify standalone usage (widget) [#315](https://github.com/imAsparky/django-tag-me/pull/315)

### Testing
- Update for standalone refactor (widget) [#315](https://github.com/imAsparky/django-tag-me/pull/315)


## [2025.12.05.2]

### Maintenance
- Update MD3 layering, add close listener (templates) [#313](https://github.com/imAsparky/django-tag-me/pull/313)
- Update prod (assets) [#313](https://github.com/imAsparky/django-tag-me/pull/313)


## [2025.12.05.1]

### Maintenance
- Update prod assets (assets) [#308](https://github.com/imAsparky/django-tag-me/pull/308)

### Documentation
- Add doc for a Django project using alpinejs/htmx and vite (howto) [#310](https://github.com/imAsparky/django-tag-me/pull/310)

### Bug Fixes
- Add tag list check to ensure addUrl created (create) [#308](https://github.com/imAsparky/django-tag-me/pull/308)
- Update build for use in django vite projects (frontend) [#311](https://github.com/imAsparky/django-tag-me/pull/311)

### Testing
- Update asset script checks (asset) [#311](https://github.com/imAsparky/django-tag-me/pull/311)


## [2025.11.24.1]

### Maintenance
- Update style with MD3 generated theme (ui) [#306](https://github.com/imAsparky/django-tag-me/pull/306)

### Testing
- Update, settings checks removed from assets (asset) [#306](https://github.com/imAsparky/django-tag-me/pull/306)


## [2025.11.22.1]

### Maintenance
- Migrate templates to MD3 and fix keyboard navigation (ui) [#304](https://github.com/imAsparky/django-tag-me/pull/304)


## [2025.11.20.2]

### Bug Fixes
- Remove default testing url in template (template) [#302](https://github.com/imAsparky/django-tag-me/pull/302)
- prevent empty tag pills from displaying (ui) [#292](https://github.com/imAsparky/django-tag-me/pull/292)


## [2025.11.20.1]

### ⚠ BREAKING CHANGES
- BREAKING: Separate SystemTag from UserTag models (models) [#282](https://github.com/imAsparky/django-tag-me/pull/282)

### Maintenance
- Update example project django (deps) [#299](https://github.com/imAsparky/django-tag-me/pull/299)

### Code Refactoring
- BREAKING: Separate SystemTag from UserTag models (models) [#282](https://github.com/imAsparky/django-tag-me/pull/282)


## [2025.11.19.1]

### Maintenance
- Update frontend to use Tailwind 4 (conf) [#296](https://github.com/imAsparky/django-tag-me/pull/296)
- Update paths/add defaults via settings (assets) [#296](https://github.com/imAsparky/django-tag-me/pull/296)
- Update production release (build) [#296](https://github.com/imAsparky/django-tag-me/pull/296)
- Update to use tokens, add no_prefix templates (templates) [#296](https://github.com/imAsparky/django-tag-me/pull/296)

### Documentation
- Add migration guide (style) [#296](https://github.com/imAsparky/django-tag-me/pull/296)

### Testing
- Update error message tests (asset) [#296](https://github.com/imAsparky/django-tag-me/pull/296)


## [2025.11.14.1]

### Features
- Add support for mobile in the browser (mobile) [#294](https://github.com/imAsparky/django-tag-me/pull/294)


## [2025.10.25.3]

### Bug Fixes
- Reinstate selected tag container pointer behavior (ui) [#286](https://github.com/imAsparky/django-tag-me/pull/286)


## [2025.10.25.2]

### Maintenance
- Update django and vite (deps) [#289](https://github.com/imAsparky/django-tag-me/pull/289)


## [2025.10.25.1]

### Bug Fixes
- Improve manifest loading robustness and type safety (asset) [#287](https://github.com/imAsparky/django-tag-me/pull/287)

### Testing
- Achieve 100% coverage for asset manifest loading (asset) [#287](https://github.com/imAsparky/django-tag-me/pull/287)


## [2025.10.23.1]

### Bug Fixes
- Resolve drag-to-reorder conflicts with text inputs and improve UX (sort) [#284](https://github.com/imAsparky/django-tag-me/pull/284)


## [2025.10.15.1]

### Bug Fixes
- Add `frontend/` & fix alpine component add functionality (tag) [#280](https://github.com/imAsparky/django-tag-me/pull/280)

### Code Refactoring
- Comment widget tests for merge (test) [#280](https://github.com/imAsparky/django-tag-me/pull/280)

### Testing
- Adjust limits for refactoring (limits) [#280](https://github.com/imAsparky/django-tag-me/pull/280)


## [2025.10.14.1]

### Maintenance
- Add front-end deps etc (git) [#277](https://github.com/imAsparky/django-tag-me/pull/277)

### Code Refactoring
- Add frontend and vite build (build) [#277](https://github.com/imAsparky/django-tag-me/pull/277)

### Testing
- Add test for frontend asset tooling (asset) [#277](https://github.com/imAsparky/django-tag-me/pull/277)


## [2025.10.13.1]

### Maintenance
- Add search_tags for all tags ever created (search) [#275](https://github.com/imAsparky/django-tag-me/pull/275)


## [2025.08.06.2]

### Bug Fixes
- Added missing import into tag_me_pills (template) [#273](https://github.com/imAsparky/django-tag-me/pull/273)


## [2025.08.06.1]

### Bug Fixes
- tag_me_pills templatetag correctly shows unicode (template) [#270](https://github.com/imAsparky/django-tag-me/pull/270)


## [2025.07.11.1]

### Bug Fixes
- Remove bg gray from tag container (template) [#268](https://github.com/imAsparky/django-tag-me/pull/268)


## [2025.07.09.1]

### Bug Fixes
- Add CookieManager with caching (js) [#266](https://github.com/imAsparky/django-tag-me/pull/266)
  > - optimize cookie parsing performance
- Reduce redundant document.cookie parsing
- Maintain getCookie() backward compatibility


## [2025.07.01.1]

### Maintenance
- Add structlog for logging (deps) [#224](https://github.com/imAsparky/django-tag-me/pull/224)
- Update for refactoring if import paths (example) [#224](https://github.com/imAsparky/django-tag-me/pull/224)

### Documentation
- Update import paths for refactor (structure) [#224](https://github.com/imAsparky/django-tag-me/pull/224)

### Features
- Add basic support for unfold-admin (unfold) [#263](https://github.com/imAsparky/django-tag-me/pull/263)

### Testing
- Update import paths (refactor) [#224](https://github.com/imAsparky/django-tag-me/pull/224)


## [2025.06.09.2]

### Bug Fixes
- Empty string removed from top of tag list (ui) [#261](https://github.com/imAsparky/django-tag-me/pull/261)


## [2025.06.09.1]

### Maintenance
- Add Aria and focus rings (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Add aria labels (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Add arrow rotation for dropdown (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Add csrf cookie cache manager (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Fix padding so consistent across browsers (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Fix small screen hamburger rotation (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Fix typos in css and escape behaviour (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Improve pill appearance and layout (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Improve tag menu transitions (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Optimise tag selection loop (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Remove logger and fix invalid syntax (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)

### Bug Fixes
- Add explicit handling of empty value list (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)
- Remove attrs breaking mozilla (ui) [#259](https://github.com/imAsparky/django-tag-me/pull/259)


## [2025.05.14.1]

### Bug Fixes
- Synced tags save ok, fix contentype query (sync) [#257](https://github.com/imAsparky/django-tag-me/pull/257)


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


