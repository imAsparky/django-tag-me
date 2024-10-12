# CHANGELOG

## v0.3.0 (2024-10-12)

### Feature

* feat(ui): Improve ux and small screen appearance #184 (#186)

* docs(how): Add new and update existing #184

* feat(widget): Improve custom template handling #185

Renamed setting from theme to template to reflect its true purpose.
Make use of get_template rather than assigning the template to
self.template_name. Improves robustness.

closes #185

* chore(conf): Add help and mgmt default settings #184

The help and management tools require urls that should be user
configurable. These are added to the bottom of the searchbar menu
so that if the dev desires, they can add custom urls. By default these
are empty so the section for display of the urls in the menu will be
hidden.

* chore(context): Add help and mgmt extracted to context #184

closes #184

* docs(how-to): Add conf for help &amp; mgmt urls #184

closes #184

* feat(ui): Improve ux and small screen appearance #184

closes #184 ([`d2f5635`](https://github.com/imAsparky/django-tag-me/commit/d2f563573efcdee4f2b0b75fc04bfd9f4c3a646a))

## v0.2.0 (2024-09-12)

### Chore

* chore(deps): bump django in /example/config/requirements (#168)

Bumps [django](https://github.com/django/django) from 5.0.7 to 5.0.8.
- [Commits](https://github.com/django/django/compare/5.0.7...5.0.8)

---
updated-dependencies:
- dependency-name: django
  dependency-type: direct:production
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`3161a14`](https://github.com/imAsparky/django-tag-me/commit/3161a149e8a6ff6bf3e587af810e17f76d868b11))

* chore(auto): prep work for autoselect new tag #175 (#176)

The current codebase requires substantial refactoring to achieve
the desired efficiency for this feature.
While the necessary backend groundwork is in place, the extensive
frontend overhaul isn&#39;t justified at this point.

closes #175 ([`c826850`](https://github.com/imAsparky/django-tag-me/commit/c826850023106e6e9b0bedf730cfc75e00d63fce))

* chore(js): Swap from toggle to close #169 (#170)

* chore(version): Bump to version 0.1.3 #169

Built and pushed to pypi

closes #169

* chore(imports): Replace missing items #169

closes #169

* chore(js): Swap from toggle to close #169

The dropdowns toggled regardless of what area of the page was
clicked, swap from toggle to close solved the problem.

closes #169

* chore(blog): Update migrations #169

closes #169 ([`764faea`](https://github.com/imAsparky/django-tag-me/commit/764faea23486d59e011dc12b3fd383ffa220c142))

* chore(tags): Update tag operations #167 (#167)

* chore(version): Bump version #675

* chore(tags): Update migrations for tags update #675

* chore(tags): Update tag operations #167

* chore(tags): Update templates #167

* chore(tags): Update migrations #167

* test(tags): Update tests #167

* chore(tags): Add/update management commands #167 ([`50fb2c5`](https://github.com/imAsparky/django-tag-me/commit/50fb2c5344fe2fe98a2dd0e8d3c848ce12f95f8d))

* chore(tags): Update for adding default tags #159 (#166)

* refactor(mgmt): Move tag management into tag mgmt sys #159

Some functions originally placed into the utils helper file have
been moved to the tag management system file, which reflects their
purpose and adds clarity to the file and function structure.

* chore(mgmt): Add/update commands to add default tags #159

* chore(field): Add default max length 255 #255

* chore(tags): Update for adding default tags #159

* chore(print): Add stdout print with color helper #159

* chore(edit): Add/refactor views for default tags #159

* chore(tags): Add/refactor for default tags #159

* chore(tags): Add management system for tags #159

* chore(logging): Update level to debug #159

* chore(tags): Updated for default tags #159 ([`206d508`](https://github.com/imAsparky/django-tag-me/commit/206d5088af4985a9f3d6ac2b6e979cbc1e9e52a5))

* chore(tag): Add context and update html #130  (#165)

* refactor(tag): Remove deprecated tag html file #130

* chore(tag): Add context and update html #130

closes #130 ([`2210bb3`](https://github.com/imAsparky/django-tag-me/commit/2210bb3fe0a310e047258527456f5dada64cfa6a))

* chore(tags): Update for tag_me changes #155 (#156)

* refactor(tags): tag_me updates #155

closes #155

* chore(tags): Update for tag_me changes #155

closes #155

* chore(tags): Add/modify  #155

closes #155

* chore(tags): Add/update #155

closes #155

* chore(tags):Update for additional functionality #155

closes #155

* refactor(mgmt):Remove &#34;&#34; for tag creation #155

closes #155

* chore(tags):Update for new functionality #155

closes #155 ([`9271293`](https://github.com/imAsparky/django-tag-me/commit/9271293e9981421fb9be4896ad1da519167f82d0))

* chore(various):  Updates to models. fields and tests #152 (#154)

* WIP(working):Before updating model fields #152

* WIP(tag_me):Updated model structure, mgmt cmds #152

* chore(system):Add return options for tag tracking #152

The system looks after creating and storing information
about the tagged fields in models, and the users access to the
tagged fields.  This commit extends a function used for collecting
and returning information to the caller in either a tuple format or
a list of objects.

closes #152

* chore(tags):Update for tag model changes #152

closes #152

* chore(tags): Update for changes in tag_me #152

closes #152

* style(black): Reformatted file #152

closes #152

* chore(fields):Add tag type #152

closes #152

* test(update): Field name changes and addition #152

closes #152 ([`8b4a789`](https://github.com/imAsparky/django-tag-me/commit/8b4a789ca9b3fb61ceb44727edab9cd64076b006))

* chore(deps): bump django from 5.0.3 to 5.0.7 (#153)

Bumps [django](https://github.com/django/django) from 5.0.3 to 5.0.7.
- [Commits](https://github.com/django/django/compare/5.0.3...5.0.7)

---
updated-dependencies:
- dependency-name: django
  dependency-type: direct:production
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`307e74c`](https://github.com/imAsparky/django-tag-me/commit/307e74cd25691cc6ddc3142fb7c2020061a2d61b))

* chore(dep): Update graphviz #145 (#147)

* docs(rtd): Add graphvix to requirements #145

closes #145

* docs(ref): Udate typo in heading #145

closes #145

* dep(doc):Update graphviz #145

closes #145 ([`4ab056f`](https://github.com/imAsparky/django-tag-me/commit/4ab056f2142c7b661980e6050a808cf706bcb91e))

* chore(mgmt): Add tag management #139 (#144)

* chore(mgmt): Add tag management #139

Add the views and urls for the tag management
interface.

closes #139

* chore(mgmt): Add template tag for app verbose #139

close #139

* chore(eg): Update migrations #139

closes #139

* docs(ref):Add/update model ref and how-to #139

closes #139

* chore(mgmt):Add/update tag management #139

closes #139

* style(black): Format files #139

closes #139 ([`776407f`](https://github.com/imAsparky/django-tag-me/commit/776407fd2ea60e85906666832916e3a886b6affa))

* chore(views): Update to use new mixins #140 (#141)

closes #140 ([`eb08305`](https://github.com/imAsparky/django-tag-me/commit/eb0830543ad0b3f6cea914a662b90d150d8d12cb))

* chore(tags): Add example tag management app #131 (#132)

* chore(tags): Add example tag management app #131

A very basic app listing all user tags and the system generated
models with tagged fields.

closes #131

* chore(config): Upated for new tag mgmt app #131

closes #131

* chore(migrations): Updated with new information #131

closes #131 ([`1d20a28`](https://github.com/imAsparky/django-tag-me/commit/1d20a2819f04bf9935758cc448624b519bc0bf8b))

* chore(eg): Add basic example app for testing #123 (#129)

This is bare bones and requires more work but will give
us what we need to work on extending the select component.

Includes endpoints for new tags. #128
Includes create permission in the widget. #128

closes #123

closes #128 ([`015fd43`](https://github.com/imAsparky/django-tag-me/commit/015fd43275341fdce3841af801a51b577880bc0a))

* chore(deps): bump django from 5.0.2 to 5.0.3 (#126)

Bumps [django](https://github.com/django/django) from 5.0.2 to 5.0.3.
- [Commits](https://github.com/django/django/compare/5.0.2...5.0.3)

---
updated-dependencies:
- dependency-name: django
  dependency-type: direct:production
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`5f7cf52`](https://github.com/imAsparky/django-tag-me/commit/5f7cf52d1169393bd5186134a86165f84083bc56))

* chore(blog): Add an example app for dev testing #124 (#127)

* chore(delete): Lost manage.py #124

Deleted file missed during the original migration of code.

closes #124

* chore(blog): Add an example app for dev testing #124

closes #124

* docs(how-to): Add instructions #124

closes #124

* chore(proj): Add deps for dev #124

closes #124 ([`cb9ad63`](https://github.com/imAsparky/django-tag-me/commit/cb9ad63a4ab52d81b637a721479349cd3a686db2))

* chore(version): Bump to 0.4.3 #119

closes #119 ([`91f8e46`](https://github.com/imAsparky/django-tag-me/commit/91f8e4603afd1c1821004f9070b902fb1c3ba306))

* chore(template): Modify template for themes #119

Update template to accept the theme changes

closes #119 ([`cc86034`](https://github.com/imAsparky/django-tag-me/commit/cc86034a0fcca6b0b9408c45416522224bb1ae2f))

* chore(template): Add select close on click away #177

closes #177 ([`d74fe2a`](https://github.com/imAsparky/django-tag-me/commit/d74fe2a40983ff1f22db871b54e306c569bedfdb))

* chore(version): Bump to 0.4.2 #114

closes #114 ([`72c450a`](https://github.com/imAsparky/django-tag-me/commit/72c450afedde3e4fbe4384fb7b310e77a031359e))

* chore(version): Bump to 0.4.1 #111

closes #111 ([`ff89269`](https://github.com/imAsparky/django-tag-me/commit/ff892694a0ddddaee3fd86a5799f58e999b3fce0))

* chore(tox): Update tox environments/deps #106

closes #106 ([`4639e3b`](https://github.com/imAsparky/django-tag-me/commit/4639e3b1e034ecb939112dfc2ba6330a877a72a2))

* chore(version): Bump to 0.4.0 #100

closes #100 ([`a64c033`](https://github.com/imAsparky/django-tag-me/commit/a64c0333b4a636371b868e23412177c70478a935))

* chore(sync): Update migrations #100

Add attribute `synchronise` to TagMeCharField that allows the synchronisation of a tag list across multiple models.

This required new models that had to be added to migrations.

closes #100 ([`1dda0b7`](https://github.com/imAsparky/django-tag-me/commit/1dda0b7879d1899cfb29bd738066a64115fda557))

* chore(sync): Add option to synchronise tag list #100

Add attribute `synchronise` to TagMeCharField that allows the synchronisation of a tag list across multiple models.  This is a very simple synchronise where if a tag is added to one model, any other model that should be synchronised will have that tag added as well.

closes #100 ([`0555300`](https://github.com/imAsparky/django-tag-me/commit/0555300b86e34fd130aee7330c16cdf0f57307a5))

* chore(version): Bump to 0.3.5 #102 ([`bb278c3`](https://github.com/imAsparky/django-tag-me/commit/bb278c3b4d7c860396b2daf7c7e063eea2dcea0b))

* chore(version): Bump to 0.3.4 #98

closes #98 ([`573ac9f`](https://github.com/imAsparky/django-tag-me/commit/573ac9f649431c8944748bf44aaed8c6eef6f6c8))

* chore(tags): Add _tag_choices to attrs #91

closes #91 ([`30e1025`](https://github.com/imAsparky/django-tag-me/commit/30e10258ebe9746eb22cf7a14b730db51e90d52d))

* chore(version): Bump to 0.3.3 #91

closes #91 ([`b506836`](https://github.com/imAsparky/django-tag-me/commit/b50683657ac171e50e5db32ae8138778e3ee2977))

* chore(tags): Handle choices set in model charfield #91

Potential existed for choices set in the model charfield to break the tags data flow.  Added handling of choices set in the charfield, they are converted to a FieldTagListFormatter list and passed to the widget.  The choices set in the charfield are treated as multi select tags.

closes #91 ([`d682d1a`](https://github.com/imAsparky/django-tag-me/commit/d682d1af3039b9a01c445c6a37b2bf9aa374110f))

* chore(version): Bump to 0.3.2 #94

closes #94 ([`8757a2b`](https://github.com/imAsparky/django-tag-me/commit/8757a2be5b58bd2d1b1004c8edfec6f7e5dacfe7))

* chore(version): Bump to 0.3.1 #92

closes #92 ([`82ea1a2`](https://github.com/imAsparky/django-tag-me/commit/82ea1a2121e12936554b077a2be4f2dc048e4d52))

* chore(version): Update supported versions #89

closes #89 ([`6fc413b`](https://github.com/imAsparky/django-tag-me/commit/6fc413b2e16c361c04f96e62df3abdfe36329c38))

* chore(version): Bump to 0.3.0 #20

Includes breaking changes. ([`eb6fb23`](https://github.com/imAsparky/django-tag-me/commit/eb6fb23fc5153b7943bcd62b8f9608c94e8250d1))

* chore(version): Bump to 0.3.0 #20

Includes breaking changes. ([`fe6a84b`](https://github.com/imAsparky/django-tag-me/commit/fe6a84b0edf33b9bb4c13b6b13fe788ad622b26b))

* chore(version): Bump to 0.2.1 #72

closes #72 ([`5fc4fd7`](https://github.com/imAsparky/django-tag-me/commit/5fc4fd74bdd8c49956ba7f366b1ef5267a136412))

* chore(version): Bump to 0.2.0 #76

closes #76 ([`ff16968`](https://github.com/imAsparky/django-tag-me/commit/ff16968d6bbdf2eea89946db87621dc670a24a46))

* chore(version): Bump to 0.1.11 #74

closes #74 ([`e680b5f`](https://github.com/imAsparky/django-tag-me/commit/e680b5f8ac9ab7b24ffd8b582ff7925adf76f5de))

* chore(version): Bump to 0.1.10 #71

closes #71 ([`ac489b3`](https://github.com/imAsparky/django-tag-me/commit/ac489b3c2e078867d6e1213ce91ffaf5d08fb167))

* chore(tags): Add custom tags choice machinery #71

Added helpers and filters to get the choices for the user/model/field for rendering in the default Django select html template.

closes #71 ([`49062b9`](https://github.com/imAsparky/django-tag-me/commit/49062b95cb440fe5b88d8e42de1376ea7a35a4fa))

* chore(version): Bump to 0.1.9 #69

closes #69 ([`8c03708`](https://github.com/imAsparky/django-tag-me/commit/8c03708ceaa6691bd6cf82c40f3a4ecbdf750d8e))

* chore(version): Bump to 0.1.8 #67

closes #67 ([`9f34536`](https://github.com/imAsparky/django-tag-me/commit/9f34536c5ddd2bfdf24670a826a0fb79884d0b0b))

* chore(version): Bump to 0.1.8 #67

closes #67 ([`359c11f`](https://github.com/imAsparky/django-tag-me/commit/359c11f7099e773fd59ae9fbb9428906653ae654))

* chore(version): Bump to 0.1.7

closes #50 ([`96707d1`](https://github.com/imAsparky/django-tag-me/commit/96707d1f88ae3e5b22dd5f0a11a018862fced1c8))

* chore(version): Bump 0.1.6

closes #64 ([`af95fb4`](https://github.com/imAsparky/django-tag-me/commit/af95fb418e6d5db5284d764cd0380c2277d3b7c3))

* chore(admin): Add admin widget, and readonly True #64

This customization allows for scenarios where appropriate tag options
        might differ between regular users and admin users. By setting the
        field as readonly in certain contexts, it ensures data consistency and
        prevents the introduction of invalid tags by regular users, while still
        allowing admins to view the full set of selected tags if needed.

Tidy up docstrings and comments

closes #62 ([`10a7f81`](https://github.com/imAsparky/django-tag-me/commit/10a7f812af96d603ba458e6933a86ea732a6b009))

* chore(attrs): Pop choice filter from attrs #62

closes #62 ([`fda15c6`](https://github.com/imAsparky/django-tag-me/commit/fda15c666e11166bf38f0402b124c10e22fea31c))

* chore(version): Bump 0.1.5 #60

closes #60 ([`ccc58c3`](https://github.com/imAsparky/django-tag-me/commit/ccc58c30d90c46285fbb50f74fa0cc7175815358))

* chore(version): Bump #58
closes #58 ([`7741f86`](https://github.com/imAsparky/django-tag-me/commit/7741f86ae099c337b1ccbfe5811f7d00ccdd718e))

* chore(default): Add widget to formfield #58

Add the default widget to formfield.  This negates the need for custom views and dynamic assignment of the widget in forms.

Refactor the custom form Charfield

closes #58 ([`bf8fac1`](https://github.com/imAsparky/django-tag-me/commit/bf8fac1b5be51315ad6cc9cb65f74e7eda304ec4))

* chore(tag): Add custom form #51

closes #51 ([`c89a4bc`](https://github.com/imAsparky/django-tag-me/commit/c89a4bc6105a7c4f37b4537774558af2de7d453c))

* chore(version): Bump to 0.1.2 ([`a2138ea`](https://github.com/imAsparky/django-tag-me/commit/a2138eae1527b4002bd7bcbc217c389cc146ea8a))

* chore(deps): Update developer env deps #45

closes #45 ([`c16949b`](https://github.com/imAsparky/django-tag-me/commit/c16949bbf4c2dee3bedfca0613c6016766e40dd2))

* chore(config): Add python 3.12 #42

closes #42 ([`b4490e3`](https://github.com/imAsparky/django-tag-me/commit/b4490e3e7209fdd9870159cbade3685cab5abc9c))

* chore(field): Add default max_length=255 #39 (#40)

closes #39 ([`04a6bbb`](https://github.com/imAsparky/django-tag-me/commit/04a6bbb816eb7451148ccb2cf1c48efce5e05fd7))

* chore(admin): Register models #37 (#38)

closes #37 ([`5e0d1f9`](https://github.com/imAsparky/django-tag-me/commit/5e0d1f9983dc57282295c0407d4c1417845db1ea))

* chore(tox): Update addopts with new tests #33 (#34)

closes #33 ([`9d0080f`](https://github.com/imAsparky/django-tag-me/commit/9d0080f1b13d924d264b62db97aa6489b18e6e99))

* chore(cov): Remove tests from coverage #21 (#23)

closes #21 ([`75b03f7`](https://github.com/imAsparky/django-tag-me/commit/75b03f775c0a91ac81b2f92a85825067bd7fb826))

* chore(tags): Port code from private repos TB and BS (#6)

* chore(conf): Update default Django settings file. #5

Change default settings file in `manage.py` and the
`BASE_DIR` path in settings.

* docs(ver): Update supported versions #5

Updated version support for only django version running on Python 3.10
and later.  Use of &#34;Structural Pattern Matching&#34; excludes all Python
before 3.10.

* chore(mgmt): Add custom migrations file #5

The custom `migrations.py` file will run all migrations and when completed
run the command `tags.py`. `tags.py` inspects all apps for tag fields
and updates the table storing them.

* chore(mgmt): Add tags updater file #5

`tags.py` inspects all apps for tagged fields.
Each model tagged field has information
collected about it and is stored in `TaggedFieldModel`.

* chore(tags): Refactor models and add functionality #5

Changed the models naming and structure to improve `tags.py`
efficiency.

* chore(tags): Add form, not completed #5

* chore(tags): Add custom tags list type #5

The `FieldTagListFormatter` inherits from a python list and overrides
existing methods, and adds some new helper methods for handling `Tag`
lists. New functionality prevents duplicate tags and also a number of
output formats.

* chore(tags): Add a tag string parser #5

This parser has been ported from Jonathan Buchanan&#39;s `django-tagging
 &lt;http://django-tagging.googlecode.com/&gt;`_

* chore(tags): Add tag handling helper functions #5

Various functions to inspect apps and get tagged and update
`TaggedFieldModel`.
Various functions to return field tags for using in `choices`

* chore(tags): Add a custom tags multi select widget #5

The custom widget is subclassed from `forms.SelectMultiple` and makes
the tuples for choices available in the form.

* tests(tags): A very minimal setup to kick off #5

* chore(pkg): Add __init__ #5

* tests(tox): Add ini file #5

* chore(tags): Add migrations #5

* chore(tags): Add custom widget html file #5 ([`2ff6f4d`](https://github.com/imAsparky/django-tag-me/commit/2ff6f4d1358bb818e620a04bc6e47e3a82be30de))

* chore(tags): Initial code migrations and organisation #1 (#4)

* chore(utils): Add parser and collections #1

* chore(db): Add forms and model fields #1

* chore(cmds): Add tagged field tables updater #1

* chore(test): Add test app #1 ([`022ec79`](https://github.com/imAsparky/django-tag-me/commit/022ec79bae0e637fb58a4de908b3b143403c7168))

* chore(pre): Remove test naming check #2 ([`c56971c`](https://github.com/imAsparky/django-tag-me/commit/c56971ccb1fd8bc974d7fcd904f5ad922b4fe9c0))

* chore(setup): Initial commit ([`bc990ef`](https://github.com/imAsparky/django-tag-me/commit/bc990ef39a0db4a85607b6050b723edac2f165b6))

### Documentation

* docs(rtd): Add graphviz to requirements (#148)

* docs(rtd): Add graphvix to requirements #145

closes #145

* docs(ref): Udate typo in heading #145

closes #145

* dep(doc):Update graphviz #145

closes #145

* docs(dep): Revert rtd yaml, graphviz added req #145

closes #145 ([`5eeaf41`](https://github.com/imAsparky/django-tag-me/commit/5eeaf412b896db8c9bc8f9bddce26619d35c59fa))

* docs(rtd): Add graphvix to requirements #145 (#146)

* docs(rtd): Add graphvix to requirements #145

closes #145

* docs(ref): Udate typo in heading #145

closes #145 ([`e95ed3e`](https://github.com/imAsparky/django-tag-me/commit/e95ed3e49634cfaa79c2419f06448a006607a39b))

* docs(ref): Add ref, update various others https://github.com/imAsparky/django-tag-me/issues/137 (#138)

* chore(version): Initial pypi release 0.1.1

* chore(deps): Add build deps #137

closes #137

* refactor(tag): Swap to use mixins for views/forms #137

When adding/updating docs it became obvious that the project would
benfit from using mixins rather than a full custom view/form.

close #137

* docs(ref): Add ref, update various others #137

closes #137 ([`a8924c8`](https://github.com/imAsparky/django-tag-me/commit/a8924c86c77ea3e4f3a3d180945623267452fd31))

* docs(how-to): Add/update contributing info #133 (#134)

closes #133 ([`7beb7b0`](https://github.com/imAsparky/django-tag-me/commit/7beb7b00ad59ee40fbf84b943e7069a446312e83))

* docs(quickstart): Add, also update readme #113

closes #113 ([`7adaa9d`](https://github.com/imAsparky/django-tag-me/commit/7adaa9d2f745b498e524277bf40dfc1079ff3d2a))

* docs(collections): Add FieldTagListFormatter #44

Update parser docs
Update how-to index

closes #44 ([`d763fde`](https://github.com/imAsparky/django-tag-me/commit/d763fde461a3fa2678f6eb117ddb785dd2f04bcf))

* docs(update): Add attribution #42

closes #42 ([`2a15efc`](https://github.com/imAsparky/django-tag-me/commit/2a15efcd3650975e6f84f4f26ae65aaf306e2729))

* docs(config): Add intersphinx mapping #42

closes #42 ([`33c2838`](https://github.com/imAsparky/django-tag-me/commit/33c2838fbfe81fae85a79c55696584f439fe0949))

* docs(how-to): Fix typos #42

closes #42 ([`6558bbf`](https://github.com/imAsparky/django-tag-me/commit/6558bbf558f0b2099a99d7f2b9358aa45f7e4704))

* docs(badge): Add docs badge, fix .yaml #26 (#27)

`.readthedocs.yaml` had a typo, this commit fixes that.

Add a readthedocs badge.

closes #26 ([`49aeff1`](https://github.com/imAsparky/django-tag-me/commit/49aeff1156342a95e2b9a91bdec6bfe447928566))

* docs(init): Add initial docs and config #24 (#25)

Create the docs folder and sphinx project with seperate source and build
folders.

Split out requirements into docs/requirements and add include with -r in
project requirements.

Add README to the index page.

Add .readthedocs.yaml file for doc builds.

Add initial config in conf.py.

Uses furo, copybutton and monokai pygments.

Includes intersphinx mapping to python and django.

closes #24 ([`ef5c7a0`](https://github.com/imAsparky/django-tag-me/commit/ef5c7a01126e5b883091cafc2326ff1eb48a3dd0))

* docs(badges): Add django and python versions #9 (#12)

closes #9 ([`056ec61`](https://github.com/imAsparky/django-tag-me/commit/056ec61b17e80aadb958705ae0a9b6f395283015))

* docs(badges): Add django and python versions #9 (#11)

* docs(badges): Add django and python versions #9

closes #9

* docs(target): Add links to python and django #9 ([`622ec97`](https://github.com/imAsparky/django-tag-me/commit/622ec972dded8af532d5ef6c71effa9ae35b9488))

* docs(badges): Add django and python versions #9 (#10)

closes #9 ([`27be938`](https://github.com/imAsparky/django-tag-me/commit/27be9386f48d4035d48e289186de2212f70d505d))

### Feature

* feat(ui): add user customisable display name #182  (#183)

* chore(example): update migrations for ui_display_name #182

closes #182

* feat(ui): add user customisable display name #182

Added `ui_display_name` field to `UserTag`. This can be
customised be the end user.

closes #182

* chore(ui): replace with addition `ui_display_name` #182

closes #182

* chore(ui): add `ui_display_name` fields #182

closes #182 ([`14afc5a`](https://github.com/imAsparky/django-tag-me/commit/14afc5a9ee05b63c33a836d1e7090c59982ba973))

* feat(build): Add python-semantic-release #177 (#178)

This added as a feature to force a new base for the
version numbers.

closes #177 ([`34ebbe7`](https://github.com/imAsparky/django-tag-me/commit/34ebbe723d84c51b36e145639fcbb760655b850d))

* feat(select): add multiselect option for tags #172 (#174)

Control multiple selections in the TagMeCharField by setting the
allow_multiple_select option to False during model field setup.
The default behavior allows multiple selections.

closes #172 ([`4658a24`](https://github.com/imAsparky/django-tag-me/commit/4658a24ec0b3af9073c7fdda6535a8e24cdd813b))

* feat(theme): Add dropdown theme functionality #119

Add setting to allow key theme and path value to choose a theme.
The theme is can be selected on a per field basis in the form init and
assign the theme name to the field widget.
Default tag_me theme is added if the dev does not create new themes.

closes #119 ([`e3f2422`](https://github.com/imAsparky/django-tag-me/commit/e3f242221576e7780ac85c967fdecfeb890b2b06))

* feat(tag): Add custom tag-me form #76

This form adds the user to all `forms.fields.TagMeCharField` attr.  The user is popped out of the attr dict in the custom widget.

closes #76 ([`65d3f68`](https://github.com/imAsparky/django-tag-me/commit/65d3f68e6dc86dd2c7ca2634d7e2b0d49bd2c81f))

* feat(views): Add custom views #49

Custom tag views have get_form_kwargs to pass model verbose name and user to the form.

closes #49 ([`ceb2c12`](https://github.com/imAsparky/django-tag-me/commit/ceb2c124c035a99f1ab65cc6a633da369a5ad04b))

* feat(parser): Add control char removal #42

Added control removal from the tag string.
Add/Improve docstrings.

closes #42 ([`31040cd`](https://github.com/imAsparky/django-tag-me/commit/31040cd5eec33bf9271632872de73f6f743229ef))

### Fix

* fix(config): update release changelog params #180 (#181)

Some settings have been added and others brought in line
with the latest version of python-semantic-release.

closes #180 ([`2300db2`](https://github.com/imAsparky/django-tag-me/commit/2300db2aa80db0e154e2470104c7633cffb0c686))

* fix(tags): Add query return type as list #160 (#162)

The tags passed to the html template was as a queryset, the
html requires a list of tags. Added return type to the query
request.

deleted an erroneaus file

closes #160 ([`8b5c8e1`](https://github.com/imAsparky/django-tag-me/commit/8b5c8e110dde4622c20b76a6b600d8641f3aae9b))

* fix(init): Update method for passing extra attrs #135 (#136)

* chore(conf): Delete unnecessary settings #135

A settings file not deleted in the initial migration has been deleted.

closes #135

* style(fmt): Black and isort #135

Run black and isort to improve format.

closes #135

* test(conf): Add settings and manage.py #135

closes #135

* fix(init): Update method for passing extra attrs #135

If tag-me is used within a view that overrides the get_form_kwargs
and injects a &#39;user&#39; key the following error is raised!
Form() got multiple values for keyword argument &#39;user&#39;

The fix was to remove the direct passing of user to the init, add a check in
form kwargs and only add the user if it was not present.

closes #135

* style(fmt): Run black and isort #135

closes #135 ([`104eb95`](https://github.com/imAsparky/django-tag-me/commit/104eb9575c2e8e279b44589f48245e0a29804fc3))

* fix(html): Remove css height #114

closes #114 ([`9743959`](https://github.com/imAsparky/django-tag-me/commit/9743959e0ca1f56c9faa3b9e9ad6cc06dced8553))

* fix(init): Move choice conversion to init #109

Conversion of choices to FieldTagListFormatter moved to init.
Testing TagMeCharfield, in some cases a model for meta data does not exist, added a fix by testing for model attr in formfield override.

closes #109 ([`1320a43`](https://github.com/imAsparky/django-tag-me/commit/1320a43b1da595ba5edf5ce879f2695d7a8a8fdd))

* fix(tags): Update return type to a list #94

Tag selection logic was returning choices as a tuple, should be flat list.

closes #94 ([`6671446`](https://github.com/imAsparky/django-tag-me/commit/66714462e02e144f35c99b33b03cc0c68263767b))

* fix(tags): Update __str__ to correct field name #92

closes #92 ([`e9164b5`](https://github.com/imAsparky/django-tag-me/commit/e9164b5262b4f898e8daa72eae2b5ca560279539))

* fix(tags): Bug reversion, clear list before adding new tags to custom fields #74

closes #74 ([`e41b90b`](https://github.com/imAsparky/django-tag-me/commit/e41b90b7f34bd6653db8ab02c02399ee7f5af836))

* fix(tags): Add include_trailing_comma to toCSV #69

The tag parser is very powerful and where there is a tag without a trailing comma, the tag is split on spaces. Update the custom model and form Charfield overridden functions to include trailing comas when getting the CSV string.

closes #69 ([`e189ab7`](https://github.com/imAsparky/django-tag-me/commit/e189ab7e5381394de717bdbe2eb2b92e9a1799ae))

* fix(admin): Add clear list before we add db tags #67

Add clear to fix switching between the same model in admin, the last models tags are also displayed in the admin of the new record displayed.

closes #67 ([`71baf28`](https://github.com/imAsparky/django-tag-me/commit/71baf2806bfc55976b635359963a17a1940ce318))

* fix(default): Revert update using defaults #60

closes #60 ([`e9fcc45`](https://github.com/imAsparky/django-tag-me/commit/e9fcc4523eca023bcc15c79fb4654cc46fcf0342))

### Refactor

* refactor(ui): Add user experience stuff #117 (#173)

* refactor(sync): Syncing Model retrieval is more robust #171

We get models using model and field names rather than
verbose, making this more robust.

closes #117

* chore(imports): Remove unused #117

closes #117

* refactor(ui): Add user experience stuff #117

Refactor/remove/combine event behavior.
Add dynamic id/names as necessary.

closes #117 ([`ba31f90`](https://github.com/imAsparky/django-tag-me/commit/ba31f901a74ba1cbdb3b42e7b083b565adce942c))

* refactor(tag-me): Swap to mixins for custom views/forms #124 (#125)

- Replaced custom forms/views with mixins.
- Commented out old code (to be removed later).
- Prework for example app and alpine component features.

closes #124 ([`d8fe72d`](https://github.com/imAsparky/django-tag-me/commit/d8fe72d8d8f3a5c50916b9bee84bcb679c5451f5))

* refactor(test): Choices tests updated #108

Removed redundant tests.
Updated broken tests due to minor changes in the code.

closes #108 ([`b6a6333`](https://github.com/imAsparky/django-tag-me/commit/b6a63337d082a7e9441ae1f37651aba997bb7c4e))

* refactor(html): Split out template to reduce size #102

Split out the tag_me template to make re-use easy, for example in custom forms.  The blk of the form is in a seperate file so that it can be easily styled.

closes #102 ([`4c48739`](https://github.com/imAsparky/django-tag-me/commit/4c48739c85639f08ac8ecc2b535b6bacba99ec2a))

* refactor(tag): Rename form #98

The custom form name was a bit verbose.  Renamed it.

closes #98 ([`e596563`](https://github.com/imAsparky/django-tag-me/commit/e5965632b9f8b1f9175f96337dbff2dcde110f3e))

* refactor(tag): Rename/remove views #98

The view names where a bite verbose.  Renamed them.
Some views didn&#39;t have get_form_kwargs, these views where removed.

closes #98 ([`09a89e6`](https://github.com/imAsparky/django-tag-me/commit/09a89e69ae1b534857539232a626729c26a089d9))

* refactor(tags): Rename field to be explicit #20

The UserTag had a field that was confusing in how it was named and required a swap within the helpers.py file.
feature now model_verbose_name
field now field_name

closes #20 ([`63cf758`](https://github.com/imAsparky/django-tag-me/commit/63cf758b6ee67a689d0968ccc06719f7a6203b34))

* refactor(tags): Rename field to be explicit #20

The UserTag had a field that was confusing in how it was named and required a swap within the helpers.py file.
feature now model_verbose_name
field now field_name

Updates downstream to users of the model completed as well.

closes #20 ([`7a94709`](https://github.com/imAsparky/django-tag-me/commit/7a9470901101eac947809c88d235d2725f001e70))

* refactor(tags): Change argument to field_name #72

Downstream refactor made the argument input confusing.  Changed from field_verbose_name to field_name.

closes #72 ([`f157dd7`](https://github.com/imAsparky/django-tag-me/commit/f157dd70a6433ece06b084c7aee7758e87ec8ce6))

* refactor(tags): Change argument to field_name #72

Downstream refactor made the argument input confusing.  Changed from field_verbose_name to field_name.

closes #72 ([`195bcbf`](https://github.com/imAsparky/django-tag-me/commit/195bcbf6cc8fdee2a05aaf02259e0ba56fb90f23))

* refactor(tags): Update template name #83

Refactoring widget html required renaming, so the widget template was updated.

closes #83 ([`f5a35eb`](https://github.com/imAsparky/django-tag-me/commit/f5a35eb2d68e329ebb83e308fb5fe5aacd21642f))

* refactor(tags): Split out html using partials #83

Split the widget template out so that users can include it into their own custom html templates with ease.

closes #83 ([`840a030`](https://github.com/imAsparky/django-tag-me/commit/840a0302ba18563636c1262125b8eb82c6609bf3))

* refactor(tags): Add tighter integration with template #56

closes #56 ([`e82727c`](https://github.com/imAsparky/django-tag-me/commit/e82727c41bcbcd37673a1d9cbfd6e9b17e68f220))

* refactor(js): Add alpineTagMeMultiSelect js #80

closes #80 ([`1b53fd4`](https://github.com/imAsparky/django-tag-me/commit/1b53fd49c756803133e719240dc3859a9a20798a))

* refactor(html): Bind select value to alpine data #78

The file needed refactor and also fixing the select values saved when the form is submitted.  The select has had the values data bound to the alpinejs selected options.

closes #78 ([`a71e0c2`](https://github.com/imAsparky/django-tag-me/commit/a71e0c2954c289b81739fff5179d9f40eebbb4c3))

* refactor(tags): Add helpers and update doc strings #50

The refactor has eliminated the circular imports by lazy loading the import at runtime.

Add a helper to return user/model/field specific tags.

closes #50

closes #35 ([`e4221d6`](https://github.com/imAsparky/django-tag-me/commit/e4221d69d687cff56d3c23ddeef0c72cd9f2d951))

* refactor(form): Update the custom form field name #58

closes #58 ([`d097b4d`](https://github.com/imAsparky/django-tag-me/commit/d097b4d560d6eb714f1cb1758a498aeb4addebbc))

* refactor(tag): Override  render #51

closes #51 ([`71b70d7`](https://github.com/imAsparky/django-tag-me/commit/71b70d7217247de4b26a044d0f87e79413796857))

* refactor(chars): Update model/form custom Charfields #48 (#54)

This commit contains a lot of small changes that are required to complete the next few issues. This includes commenting out the custom tag creation and automatic table updates due to circular references after this refactor.

Print statements have been left in for the completion of the next few issues

closes #48 ([`fa1a8b6`](https://github.com/imAsparky/django-tag-me/commit/fa1a8b6a86c0ccc8fe2b9397862ee599a53fcfef))

* refactor(chars): Update model/form custom Charfields #48

This commit contains a lot of small changes that are required to complete the next few issues. This includes commenting out the custom tag creation and automatic table updates due to circular references after this refactor.

Print statements have been left in for the completion of the next few issues

closes #48 ([`6c1efad`](https://github.com/imAsparky/django-tag-me/commit/6c1efadf3137c9647df8ad0c42b3a2d6a03be0e3))

* refactor(util): Update collections #44

Refactor collections to improve readability.
Add docstrings
Add type hint to parser output.

closes #44 ([`4958ce5`](https://github.com/imAsparky/django-tag-me/commit/4958ce5d3e1f325804140d33a2f3d202aaa6f37a))

* refactor(various): Improvements found adding tests #30 (#36)

* refactor(various): Improvements found adding tests #30

While adding tests for `helpers.py`, several improvements where found
and implemented.

closes #30

* test(helpers): Add tests for helpers #30

closes #30 ([`f4ef093`](https://github.com/imAsparky/django-tag-me/commit/f4ef09354bb8369d97ce1fd172ba6df7b9c3f8d4))

### Test

* test(parser): Add tests #42

closes #42 ([`c692030`](https://github.com/imAsparky/django-tag-me/commit/c692030f00e7d34cd8a185984c660d65959f4114))

* test(cmd): Add tests for custom mgmt commands #31 (#32)

* refactor(cmds): Using call_command to run tags #31

While completing tests improvements where found in the management
commands.

closes #31

* test(cmd): Add tests for custom mgmt commands #31

closes #31 ([`6025b43`](https://github.com/imAsparky/django-tag-me/commit/6025b431653fb0625b43d6f525a6abeec7f116cc))

* test(tags): Add edit_string tests #19 (#22)

Added tests for parsers `edit_string_for_tags`.

Added additional tests into collections that cover the missing coverage
for the tag parser.

Refactored tests_collections for easier reading.

closes #19
closes #18 ([`5dfc46e`](https://github.com/imAsparky/django-tag-me/commit/5dfc46ecf44e96120c3c06f4be3b06bada6d03b6))

* test(tags): Refactor model field and add tests #16 (#17)

* test(tags): Refactor model field and add tests #16

While adding tests several improvements where found in
`TagMeCharField`.

closes #16

* test(tags):Add form field tests #14

While adding tests several improvements where found in
`TagMeCharFieldForm`.

closes #14 ([`87e7452`](https://github.com/imAsparky/django-tag-me/commit/87e7452402191ecf137621991bf209d826780c2c))

* test(tags): Refactor form field and add tests #14 (#15)

While adding tests several improvements where found in
`TagMeCharFieldForm`.

closes #14 ([`f1f29c6`](https://github.com/imAsparky/django-tag-me/commit/f1f29c67ea26f9c5ce987cd88b176cf63dc07260))

* test(tags): Add collection and model field tests #7 (#8)

* test(field): Update model field and add tests #7

While adding tests several improvements where found in `TagMeCharField`.

closes #7

* test(collection): Update collections and add tests #7

While adding tests several improvements where found in `FieldTagListFormatter`.

closes #7 ([`02057aa`](https://github.com/imAsparky/django-tag-me/commit/02057aa39b92ddf8fed4cad2883c065b72e43d34))

### Unknown

* :memo: build(version): Bump to version - 0.2.0.

Automatically generated by python-semantic-release ([`e6ada73`](https://github.com/imAsparky/django-tag-me/commit/e6ada73ea29aa905366cce8ffaa1611f0599cd42))

* 0.1.0 (#179)

Automatically generated by python-semantic-release

Co-authored-by: semantic-release &lt;semantic-release&gt; ([`a81b24e`](https://github.com/imAsparky/django-tag-me/commit/a81b24e92649873a832f5b3081b30b81fdbe08dd))

* chore(tags):Add dynamic add tag url #163 (#164)

closes #163 ([`c04ec0f`](https://github.com/imAsparky/django-tag-me/commit/c04ec0f22d3eb6030b280f6f86cdf48a357d7871))

* Feature to add and refresh with new tags. Issue 160 fixes workarounds. (#161)

Co-authored-by: Robin Chew &lt;me@robin.com.au&gt; ([`06286db`](https://github.com/imAsparky/django-tag-me/commit/06286dbe518ba292d4ff6523612edb2a94498c14))

* core(tags):Add fixtures for user tags #151 (#158)

closes #151 ([`cb11ad2`](https://github.com/imAsparky/django-tag-me/commit/cb11ad24a635dede1e47b8122cf3eda1434b6ddf))

* chore(meta):Add field for meta data #121 (#157)

closes #121 ([`e06b47e`](https://github.com/imAsparky/django-tag-me/commit/e06b47e99fcc1a5cab98e2455f91ef8717477146))

* chore(doc):Add _static folder for graphiz #149 (#150)

closes #149 ([`b22788b`](https://github.com/imAsparky/django-tag-me/commit/b22788b5756610222df7342bfb8cc0a98650327b))

* chore(eg):Add new cookiecutter example project #142 (#143)

* chore(eg): Delete original example #142

Starting a new example project from our cookiecutter.

closes #142

* chore(eg):Add new cookiecutter example project #142

closes #142

* chore(app): Add blog #142

closes #142

* chore(user): Add user fixtures #142

closes #142

* chore(template): Add blog #142

closes #142

* chore(app): Updates for new blog app #142

closes #142

* chore(auth): Update sign in/out forms #142

closes #142 ([`88f32fc`](https://github.com/imAsparky/django-tag-me/commit/88f32fc0ab2b5f4240054855671946bac3cfaeea))

* chore(version_ Bump to 0.3.5 #102

closes #102 ([`22a9e7a`](https://github.com/imAsparky/django-tag-me/commit/22a9e7af5a6932932a9c8b759e24d5e33086c1fd))

* tests(refactor): Update tests to reflect changes in tags format when saved #87

closes #87 ([`9914425`](https://github.com/imAsparky/django-tag-me/commit/9914425eff53b60c1213a4bafc1027b45f137754))

* tests(tags): Rename field to be explicit #20

The UserTag had a field that was confusing in how it was named and required a swap within the helpers.py file.
feature now model_verbose_name
field now field_name

closes #20 ([`fe125a5`](https://github.com/imAsparky/django-tag-me/commit/fe125a5e8d49920f820226bf4b4efb4be1a9e15f))

* Revert &#34;refactor(chars): Update model/form custom Charfields #48&#34;

This reverts commit 6c1efadf3137c9647df8ad0c42b3a2d6a03be0e3. ([`af677cf`](https://github.com/imAsparky/django-tag-me/commit/af677cf3c8d3494956a135190a608de03e1c3235))

* tests(matrix): Remove dj32, add dj50 #46

closes #46 ([`6ed0158`](https://github.com/imAsparky/django-tag-me/commit/6ed01582f823c479f478fe5747cb09c91ba46fe7))

* tests(util): Add/Extend collections tests #44

Extend tests with hypothesis.
Add targeted tests to helper functions.

Re-organise tests into logical classes.
Add doc strings

closes #44 ([`aa2ba01`](https://github.com/imAsparky/django-tag-me/commit/aa2ba01ce9e81975cd3f7bfd34ab14849bed7136))

* docs(parser) Add basic useage how-to #28 (#29)

closes #28 ([`a9da43b`](https://github.com/imAsparky/django-tag-me/commit/a9da43bed367e66722a6c177ce670e6e797b395a))

* Issue 9 (#13)

* docs(badges): Add django and python versions #9

closes #9

* docs(rst): Fix typo in target #9 ([`3384234`](https://github.com/imAsparky/django-tag-me/commit/3384234065794b3ee9caa0fe1b157703bb19dcc3))

* Merge pull request #3 from imAsparky/issue-2

chore(pre): Remove test naming check #2 ([`595d1ca`](https://github.com/imAsparky/django-tag-me/commit/595d1cab2af72cde69e5489816c2fe861c77175b))

* Update issue templates ([`7bbfee0`](https://github.com/imAsparky/django-tag-me/commit/7bbfee084f42b50b4a384fdd5d584c4cea09febf))
