
.. include:: ../extras.rst.txt
.. highlight:: rst
.. index:: working-with-the-fieldtaglistformatter-in-django ; Index

.. _working-with-the-fieldtaglistformatter-in-django:

================================================
Working with the FieldTagListFormatter in Django
================================================

Overview
========

FieldTagListFormatter is a custom list object designed to streamline tag management in Django.
It's the core component behind the custom `TagMeCharField` field. Key features include:

* **Duplicate Prevention:** Ensures each tag appears only once in a tag list.
* **Flexible Input:** Handles dictionaries, lists, sets, and strings for tag input.

**Purpose**

The `FieldTagListFormatter` simplifies tagging in your Django applications, providing a user-friendly
and robust way to manage tags associated with your models.

|


.. _fieldtaglistformatter-class:

The FieldTagListFormatter Class
===============================

The `FieldTagListFormatter` class provides the following key methods for managing tags:

* **__init__(tags=None)**: Initializes the tag list. Can optionally accept initial tags in various formats.

* **add_tags(tags)**: Adds one or more tags to the list, ensuring uniqueness. Handles dictionaries, lists, sets, and strings.

* **del_tags(tags)**: Removes one or more tags from the list. Handles dictionaries, lists, sets, and strings.

* **_is_valid_tag(tag)**: Internal method used to check if a tag is a valid string (and not null).

* **_get_tag_list(tags)**: Internal method to extract and validate tags from different input formats.

.. note::

    `FieldTagListFormatter` also inherits standard list methods for additional tag manipulation.

|

.. _fieldtaglistformatter-usage:

Usage
=====

**Instantiation**

* **Creating an empty tag list:**

   .. code-block:: python
      :caption: Creating an empty FieldTagListFormatter

      my_tags = FieldTagListFormatter()

* **Creating a tag list with initial tags:**

   .. code-block:: python
      :caption: Initializing FieldTagListFormatter with tags

      my_tags = FieldTagListFormatter(["python", "django", "web-development"])

**Adding Tags**

* **From a dictionary:**

   .. code-block:: python
      :caption: Adding tags from a dictionary

      my_tags.add_tags({"tags": ["design", "ui"]})
      my_tags.add_tags({"tags": "django, alpine js, htmx"})

.. caution::

    The dictionary must contain a `tags` key.

* **From a list or set:**

   .. code-block:: python
      :caption: Adding tags from a list or set

      my_tags.add_tags(set(["tutorial", "guide"]))

* **From a comma-separated string:**

   .. code-block:: python
      :caption: Adding tags from a comma-separated string

      my_tags.add_tags("django, alpine js, htmx")

**Removing Tags**

* **Using a list or set:**

   .. code-block:: python
      :caption: Removing tags using a list or set

      my_tags.del_tags(["django", "alpine js"])

* **Using a comma-separated string:**

   .. code-block:: python
      :caption: Removing tags using a comma-separated string

      my_tags.del_tags("frontend, guide")

**Important Notes**

.. note::
   **Duplicate Prevention:** The `add_tags` method automatically prevents duplicates.

.. note::
   **Case Sensitivity:**  Tag comparisons are case-sensitive.

.. note::
   **Tag Validation:** The class ensures only valid strings (not null values) are added to the list.

|

.. _fieldtaglistformatter-integration:

Integration with Django Models
==============================

**Using the `TagMeCharField`**

The `FieldTagListFormatter` class is the core component behind the custom `TagMeCharField` field. Here's how you
would typically integrate it into a Django model:

.. code-block:: python
   :caption: Defining a Django model with the TagMeCharField

   from django.db import models
   from tag_me.models.fields import TagMeCharField

   class MyModel(models.Model):
       ...  # Other model fields
       tags = TagMeCharField()

**Typical Usage Scenarios**

* **After Creating a MyModel Instance:**

   .. code-block:: python
      :caption: Adding tags to a MyModel instance

      my_instance = MyModel.objects.create(...)
      my_instance.tags.add_tags(["tutorial", "python"])
      my_instance.save()  # Important to save changes

* **Updating Tags:**

   .. code-block:: python
      :caption: Modifying tags on a MyModel instance

      my_instance.tags.del_tags("python")
      my_instance.tags.add_tags("machine-learning")
      my_instance.save()


**Notes**

.. note::

    **Case Sensitivity:** Tags are case-sensitive.

.. important::

   See :ref:`how-to-tag-parser` for information on tag input examples.
