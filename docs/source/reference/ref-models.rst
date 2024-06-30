.. highlight:: rst
.. index:: models ; Index


.. _ref-models:

=====
Model
=====


UserTag
=======

* **Core Fields:**
   - `name`: The actual text label of the tag.
   - `slug`: A URL-friendly version of the tag name, ensuring uniqueness.
   - `user`: A foreign key relationship to the user who created the tag.
   - `content_type`: A foreign key to the `ContentType` model, identifying the tagged object's model type.
   - `model_verbose_name`:  A human-readable name of the model being tagged.
   - `field_name`: The name of the specific field within the model that is tagged.
   - `comment`: An optional comment associated with the tag.

* **Key Relationships:**
   - Many-to-one relationship with `User`: A user can create multiple tags.
   - Many-to-one relationship with `ContentType`: A tag can be applied to multiple instances of the same content type.

* **Synchronization Functionality:**
   - The `save` method includes logic to handle tag synchronization across related content types based on the `TagMeSynchronise` model configuration.

**Simplified Diagram:**

Here's a simplified diagram illustrating the core structure and relationships of the `UserTag` model:

.. graphviz::

   digraph {
       rankdir=LR;
       User [shape=box, style=filled, fillcolor=lightblue, label="User"];
       UserTag [shape=box, style=filled, fillcolor=lightgreen, label="UserTag"];
       ContentType [shape=box, style=filled, fillcolor=lightyellow, label="ContentType"];

       User -> UserTag [label="", arrowhead=vee];
       UserTag -> ContentType [label="", arrowhead=vee];
   }

**Key Points:**

* The `UserTag` model acts as a bridge between users, content types (models), and the specific fields within those models that are tagged.
* The synchronization logic in the `save` method adds complexity, but it's a crucial feature for maintaining consistency across related tagged objects.

Feel free to ask if you'd like any clarification or have any further questions about the diagram or the model itself.

