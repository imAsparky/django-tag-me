
.. include:: ../extras.rst.txt
.. highlight:: rst
.. index:: how-to-tagged-field; Index


.. _how-to-tagged-field:


======================================================
TaggedField Model: A Guide to the tag management tools
======================================================

The django-tag-me library provides a simple centralised tag management model.

1. **TaggedFieldModel:** For storing model and tagged field information.


The ``TaggedFieldModel`` Model
------------------------------

The ``TaggedFieldModel`` model is designed to store all the data for models with tagged fields.

.. tip::

   These fields are auto populated during the migration process.

   The only editable field in this model is the ``default_tags``.


**Fields:**

* **content (ForeignKey):**  References the django content id (required).
* **model_name (CharField):**  References the ``django model name`` of the model being tagged (required).
* **model_verbose_name (CharField):**  Stores the verbose name of the tagged model (required).
* **field_name (CharField):**  The name of the field being tagged (required).
* **field_verbose_name (CharField):**  Stores the verbose name of the models tagged field (required).
* **tag_type (CharField):**  A description of the tag type, ``user`` or ``system`` (required).
* **default_tags (CharField):** A convenience to allow admins to pre-populate user tags with some defaults (optional). Can be added using admin.

Constraints
-----------

.. code-block:: python

      constraints = [
            models.UniqueConstraint(
                fields=[
                    "content",
                    "model_name",
                    "model_verbose_name",
                    "field_name",
                    "field_verbose_name",
                ],
                name="unique_tagged_field_model",
            ),
        ]



