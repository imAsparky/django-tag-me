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

   pip install git+https://github.com/imAsparky/django-tag-me.git

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

   Use of the custom 'tag-me' model form is required for the tags widget to function correctly.

|

.. code-block:: python

   from tag_me.forms import TagMeModelForm
   from .models import MyModel

   class MyModelForm(TagMeModelForm):

       class Meta:
           fields = ['my_tagged_field']

|

**Views**

|

.. note::

    For convenience, use the custom 'tag-me' views. Alternatively, you can use standard Django views, but you'll need to override the `get_form_kwargs` method to provide necessary information to the form.

    See below for an example.

|

.. code-block:: python

    from tag_me.views.generic import TagMeCreateView
    from .forms import MyModelForm
    from .models import MyModel

    class MyModelCreateView(TagMeCreateView)
        model = MyModel
        form_class = MyModelForm
        etc ...

|

Alternatively, override `get_form_kwargs` in your view to supply the user the custom form.

|

.. code-block:: python

    def get_form_kwargs(self):
    """This method adds form keyword arguments.

    Adding kwargs here makes them available in the forms.  The view passes
    the kwargs to forms where they can be popped out in __init__
    """

    kwargs = super().get_form_kwargs()
    # Add user_id to kwargs
    kwargs["user"] = self.request.user

    return kwargs

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
