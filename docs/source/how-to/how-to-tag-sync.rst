.. include:: ../../extras.rst.txt
.. highlight:: rst
.. index:: how-to-tag-sync ; Index


.. _how-to-tag-sync:


====================================================================
UserTag Model: A Guide to User-Specific Tagging with Synchronization
====================================================================

The django-tag-me library provides two core components for flexible tagging:

1. **UserTag Model:** For creating user-specific tags on specific fields.

2. **TagMeCharField Field:** A custom Django model field that enhances your models with tagging capabilities and controls tag synchronization.

The ``UserTag`` Model
---------------------

The ``UserTag`` model is designed to enable users to create and manage tags associated with specific fields in your Django models. It provides a flexible way to categorize and filter data based on user-defined tags.

**Fields:**

* **user (ForeignKey):**  References the user who created the tag (required).
* **content_type_id (ForeignKey):**  References the ``ContentType`` of the model being tagged (required).
* **model_verbose_name (CharField):**  Stores the verbose name of the tagged model (optional).
* **comment (CharField):**  A short comment or description of the tag (optional).
* **field_name (CharField):**  The name of the field being tagged (required).

**Constraints:**

* **Unique Constraint:**  Ensures that each user can only have one tag with the same name, field, and content type combination.


The ``TagMeCharField`` Field
----------------------------

The ``TagMeCharField`` is a custom Django model field that provides an easy way to add tagging functionality to any ``CharField`` in your models. It handles tag validation, formatting, database storage, and controls tag synchronization.

**Enabling Synchronization:**

To enable tag synchronization for a ``TagMeCharField`` field, simply set the `synchronise` attribute to `True` when defining the field in your model:

.. code-block:: python

   from django.db import models
   from tag_me.models import TagMeCharField

   class MyModel(models.Model):
       my_field = TagMeCharField(synchronise=True)


