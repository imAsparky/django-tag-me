.. highlight:: rst
.. index:: helpers ; Index


.. _ref-helpers:

======
Helper
======


**Overview:**

This file contains utility functions to manage tagged fields and their synchronization within your Django project, leveraging your `TagMeCharField` custom field for tagging functionality.  The key functionalities include:

* **Maintaining a Registry of Tagged Fields:**  The `update_models_with_tagged_fields_table` function keeps track of which models and fields are using `TagMeCharField`. It stores this information in the `TaggedFieldModel` database table, providing a central reference point.

* **Managing Tag Synchronization:** The `update_fields_that_should_be_synchronised` function identifies which fields have the `synchronise` attribute set to `True`. It updates the `TagMeSynchronise` model (specifically the 'default' configuration) to ensure that tags applied to those fields are propagated to other relevant content types.

* **Generating Choices for Forms:** Several functions are dedicated to generating choices for form fields, allowing users to select from:
    * Models that have tagged fields (`get_models_with_tagged_fields_choices`)
    * Specific tagged fields within a model (`get_model_tagged_fields_choices`)
    * A user's own tags for a particular field and model (`get_user_field_choices_as_list_tuples`)

**Simplified Diagram:**

Here's a simplified representation of the relationships between the core models and functions involved:

.. graphviz::

   digraph {
       rankdir=LR;
       User [shape=box, style=filled, fillcolor=lightblue, label="User"];
       UserTag [shape=box, style=filled, fillcolor=lightgreen, label="UserTag"];
       TaggedFieldModel [shape=box, style=filled, fillcolor=lightcoral, label="TaggedFieldModel"];
       TagMeSynchronise [shape=box, style=filled, fillcolor=lightyellow, label="TagMeSynchronise"];
       TagMeCharField [shape=ellipse, style=filled, fillcolor=lavender, label="TagMeCharField"];

       User -> UserTag [label="", arrowhead=vee];
       TagMeCharField -> TaggedFieldModel [label="Registered in", arrowhead=vee, style=dashed]; 
       TagMeCharField -> TagMeSynchronise [label="Synchronised with (if enabled)", arrowhead=vee, style=dashed];
   }
**Key Points:**

* **`TaggedFieldModel`:**  This model acts as a central registry of fields that utilize the `TagMeCharField` custom field.
* **`TagMeSynchronise`:** This model, particularly the "default" instance, holds configuration data determining which tagged fields should have their tags synchronized across related content types.
* **Functions:** The utility functions primarily serve to interact with these two models, either updating their information or retrieving data to populate form choices dynamically.
* **User Interaction:** Users indirectly interact with this system when they select models, fields, or their own tags in forms generated using the utility functions. These choices then drive the tagging and synchronization processes.

