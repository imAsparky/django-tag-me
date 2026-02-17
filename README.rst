=================
**Django Tag Me**
=================

|

**Version = 2026.02.17.1**

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

Add tags to any Django model field—with a polished widget, per-user tag customization, and optional synchronization across models.

|

Features
--------

- **Easy setup** — Add ``TagMeCharField`` to your model
- **Beautiful widget** — Searchable dropdown with tag pills, powered by Alpine.js
- **User tags** — Each user gets their own customizable tag set per field
- **System tags** — Define default tags available to all users
- **Tag synchronization** — Keep tags in sync across related models
- **Form integration** — Drop-in mixin for your model forms
- **Template tags** — Display tags as styled pills
- **Model rename resilient** — Uses ContentType FK lookups, not model name strings

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

Installation
------------

.. code-block:: bash

    pip install django-tag-me

See the `documentation <https://django-tag-me.readthedocs.io/>`_ for setup and usage instructions.

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