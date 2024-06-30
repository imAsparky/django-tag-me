.. include:: ../../extras.rst.txt
.. highlight:: rst
.. index:: how-to-quickstart ; Index


.. _how-to-quickstart:

=================
Tag-Me Quickstart
=================

**Minimum Requirements**

* Python version 3.10 or greater.
* Django 4.0 or greater.


Installation
============

**Install the 'django-tag-me' package using pip:**

.. code-block:: bash

   pip install django-tag-me

|


**Add `tag-me` to your installed apps.**

|

.. code-block:: python

    INSTALLED_APPS = [
    "tag_me",
    ]

|



Once installed, add the models and static files to your Django project:


|

.. code-block:: bash

    python3 manage.py collectstatic

    python3 manage.py makemigrations

    python3 manage.py migrate

|

**After successful migration, you should see output similar to the following in your console:**

|

.. code-block:: bash

        INFO    2024-04-03 07:40:47,367 INFO    MainThread       helpers.py:61
                 (/venv/lib/python3.12/site-packages/tag_me/utils/helpers.py :
                 61) tag_me.utils.helpers.update_models_with_tagged_fields_table:    Updated Your Model Name :
                 your field name
        INFO    2024-04-03 07:40:47,369 INFO    MainThread        models.py:134
                 (/venv/lib/python3.12/site-packages/tag_me/models.py : 134)
                 tag_me.models.check_field_sync_list_lengths: You have no field tags listed that require
                 synchronising

    Updating Tagged Models Table.
    SUCCESS: Tagged Models Table, and Synchronised Fields updated.

|

**Add Alpine.js and 'tag-me' scripts to your base.html**

*Alpine.js is a lightweight JavaScript framework that adds reactivity to your HTML. It's required for the 'tag-me' functionality.*

.. note::

   The CDN for the alpine components below may not be the latest. Please see https://alpinejs.dev/essentials/installation
   and https://alpinejs.dev/plugins/focus for the latest versions.

.. important::

   Ensure the Alpine Focus script is included before Alpine's core JS file, as per the Alpine Focus documentation!

|

.. code-block:: html

   <head>
   <script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>

   <script defer src="https://unpkg.com/alpinejs@3.13.1/dist/cdn.min.js"></script>

   <script src="{% static 'tag_me/tag_me_multi_select.js' %}"></script>
   </head>

|

Usage
=====

|

**Add a 'tag-me' tag to your Django model.**

|

Tagging allows you to associate flexible keywords or categories with your model instance fields.  It is possible to have more than one model field with tagging functionality.

|

.. tip::

   While not required, adding a user-friendly `verbose_name` will improve the users experience. `verbose_name` is used throughout the 'tag-me' package as an identifier.

    If you dont provide a `verbose_name`, the Django default will be used.

|

.. code-block:: python

   from django.db import models
   from tag_me.db.models.fields import TagMeCharField

   class MyModel(models.Model)

       my_tagged_field = TagMeCharField(
           max_length=255,
           null=True,
           blank=True,
           verbose_name="My Tagged Field",  # User-friendly label
           help_text= "How to use tag-me TagMeCharField.",
           )


|

**Forms**

|

.. important::

   Use of the custom 'tag-me' form mixin is required for the tags widget to function correctly.

See below for an example.

|

.. code-block:: python

   from django import forms
   from tag_me.db.forms.mixins import TagMeModelFormMixin
   from tag_me.widgets import TagMeSelectMultipleWidget
   from .models import MyModel

   class MyModelForm(TagMeModelFormMixin, forms.ModelForm):

       class Meta:
           model = MyModel
           fields = ['my_tagged_field']

       widgets = {
            "my_tagged_field": TagMeSelectMultipleWidget(),
        }

|

**Views**

|

.. important::

    Use of the custom 'tag-me' view mixin is required for the tags widget to function correctly.

See below for an example.

|

.. code-block:: python

    from django.views.generic import CreateView
    from tag_me.db.mixins import TagMeViewMixin
    from .forms import MyModelForm
    from .models import MyModel

    class MyModelCreateView(TagMeViewMixin, CreateView)
        model = MyModel
        form_class = MyModelForm
        etc ...

|


Creating Tags
=============

|

Currently, users can only create tags through the Django administration panel. Functionality for regular users to create tags is planned for future development.

|

Choices
-------

|

You may use the model choices machinery to add a fixed set of tags.

|

.. warning::

    Using the model choices mechanism to define tags bypasses Django's built-in choices validation. This method provides a simple way to add fixed tags, and is a convenience for you, the developer.

    See example below.

|

.. code-block:: python

    from django.db import models
    from django.utils.translation import pgettext_lazy as _

    class MyModel(models.Model)

        class ApprovalStatus(models.TextChoices):
            """Approval Status choices."""

            APPROVED = "APPROVED", _(
                "Status",
                "Approved",
            )
            NOT_REVIEWED = "NOT_REVIEWED", _(
                "Status",
                "Not Reviewed",
            )
            REJECTED = "REJECTED", _(
                "Status",
                "Rejected",
            )

        my_tagged_field = TagMeCharField(
            max_length=255,
            choices=ApprovalStatus.choices,
            default=ApprovalStatus.NOT_REVIEWED,
            null=True,
            blank=True,
            verbose_name="My Tagged Field",
            help_text= "How to use tag-me TagMeCharField with choices.",
            )

|

.. important::

    During initialization, `TagMeCharField` internally converts your `choices` into a tag representation for seamless integration.
