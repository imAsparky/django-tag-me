=================
**Django Tag Me**
=================

|

**Version = 2026.02.24.1**

|

*Simple, flexible tagging for Django.*

|

.. image:: https://github.com/imAsparky/django-tag-me/actions/workflows/main_PR.yaml/badge.svg
   :alt: Tests
   :target: https://github.com/imAsparky/django-tag-me/actions/workflows/main_PR.yaml
.. image:: https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FimAsparky%2Fdjango-tag-me%2Fmain%2Fpyproject.toml&query=project.dependencies&logo=Django&label=Versions&labelColor=%23092E20
   :alt: Django Version Badge
   :target: https://docs.djangoproject.com/en/4.2/
.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FimAsparky%2Fdjango-tag-me%2Fmain%2Fpyproject.toml&logo=Python
   :alt: Python Version Badge
   :target: https://devdocs.io/python~3.10/
.. image:: https://www.repostatus.org/badges/latest/active.svg
   :alt: Project Status: Active
   :target: https://www.repostatus.org/#active
.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. image:: https://readthedocs.org/projects/django-tag-me/badge/?version=latest
   :target: https://django-tag-me.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

|

Add tags to any Django model field—with a polished widget, per-user tag
customization, and automatic resilience to model renames.

|

Features
--------

- **Easy setup** — Add ``TagMeCharField`` to your model and go
- **Beautiful widget** — Searchable dropdown with tag pills, powered by Alpine.js
- **User tags** — Each user gets their own customizable tag set per field
- **System tags** — Define default tags available to all users
- **Tag synchronization** — Keep tags in sync across related models
- **Model rename resilient** — FK-based lookups with automatic orphan detection and repair
- **CLI diagnostics** — Health checks, orphan repair, and built-in troubleshooting via ``tag_me`` command
- **Structured logging** — Observability via structlog for production monitoring
- **Form integration** — Drop-in mixin for your model forms
- **Template tags** — Display tags as styled pills

|

Quick Example
-------------

.. code-block:: python

    # models.py
    from tag_me.models import TagMeCharField

    class Article(models.Model):
        tags = TagMeCharField(blank=True)
        category = TagMeCharField(choices=CategoryChoices.choices, system_tag=True)

.. code-block:: python

    # forms.py
    from tag_me.forms import TagMeModelFormMixin

    class ArticleForm(TagMeModelFormMixin, forms.ModelForm):
        class Meta:
            model = Article
            fields = ["tags", "category"]

See the `Quickstart <https://django-tag-me.readthedocs.io/en/latest/quickstart.html>`_
for the full setup including templates and frontend requirements.

|

Widget Preview
--------------

**Dropdown with tag options**

.. image:: https://raw.githubusercontent.com/imAsparky/django-tag-me/main/docs/source/imgs/tag_dropdown_with_options.png
   :alt: Tag dropdown with options

|

**Search and filter tags**

.. image:: https://raw.githubusercontent.com/imAsparky/django-tag-me/main/docs/source/imgs/tag_dropdown_search.png
   :alt: Tag dropdown search functionality

|

Model Rename Resilience
-----------------------

Rename your Django models without breaking tags. Tag-me uses ContentType
foreign keys instead of model name strings, and automatically detects and
merges orphaned records during migration.

.. code-block:: bash

    # Rename your model, then:
    python manage.py makemigrations   # answer "yes" to rename prompt
    python manage.py migrate          # tag-me handles the rest

    # Verify everything is clean:
    python manage.py tag_me check

See `How to Upgrade to FK Lookup <https://django-tag-me.readthedocs.io/en/latest/how-to/upgrade-fk-lookup.html>`_
for details on the FK-based system.

|

Management Command
------------------

Tag-me includes a CLI for diagnostics and administration:

.. code-block:: bash

    python manage.py tag_me populate              # create/update tags
    python manage.py tag_me check                 # data integrity audit
    python manage.py tag_me fix-orphans --dry-run # preview orphan repair
    python manage.py tag_me help                  # built-in documentation

Tag population runs automatically after every ``migrate``. The CLI exists for
diagnostics, manual repair, and single-user operations.

See `How to Use the Tag-me CLI <https://django-tag-me.readthedocs.io/en/latest/how-to/management-command.html>`_
for the full guide.

|

Installation
------------

.. code-block:: bash

    pip install django-tag-me

See the `documentation <https://django-tag-me.readthedocs.io/>`_ for setup and
usage instructions.

|

Links
-----

- `Documentation <https://django-tag-me.readthedocs.io/>`_
- `Source Code <https://github.com/imAsparky/django-tag-me>`_
- `Issue Tracker <https://github.com/imAsparky/django-tag-me/issues>`_

|

Credits
-------

- Dropdown interface adapted from `alpinejs-multiselect <https://github.com/alexpechkarev/alpinejs-multiselect/>`_
- Built with `Django Cookiecutter <https://github.com/imAsparky/django-cookiecutter>`_
