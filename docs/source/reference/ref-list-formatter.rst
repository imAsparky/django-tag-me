.. highlight:: rst
.. index:: tag-list-formatter ; Index


.. _ref-tag-list-formatter:

==================
Tag List Formatter
==================


**Overview**

This class is a custom list implementation designed specifically for handling tags within your Django project. It inherits from the built-in Python `list` class, but it adds several important features and modifications to make it more suitable for working with tags:

* **Duplicate Prevention:**  It ensures that each tag in the list is unique, preventing any duplicate entries. This is crucial for maintaining a clean and organized list of tags.

* **Custom Tag Manipulation Methods:** It provides methods like `add_tags` and `del_tags` that accept either strings or lists of tags. These methods leverage the `parse_tags` utility function to easily add or remove multiple tags at once.

* **Validation:**  It includes methods to validate tags (`_is_valid_tag`) and tag containers (dictionaries, lists, sets, or strings) (`_is_valid_tag_container`). This helps prevent invalid or malformed data from entering the tag list.

* **Conversion Methods:**  It offers methods to convert the tag list to different formats:
    * `toCSV`: Returns a comma-separated string representation of the tags.
    * `toDict`: Returns a dictionary with the tags under the key "tags."
    * `toJson`: Returns a JSON string representation of the tags.
    * `toList`: Returns the tags as a standard Python list.

* **Overridden List Methods:** It overrides various standard list methods (e.g., `append`, `extend`, `insert`, `remove`) to maintain the unique tag constraint and ensure proper validation.

**Simplified Diagram (Graphviz)**

.. graphviz::

   digraph {
       rankdir=LR;
       FieldTagListFormatter [shape=box, style=filled, fillcolor=lightblue, label="FieldTagListFormatter"];
       list [shape=ellipse, style=filled, fillcolor=lavender, label="list (built-in)"];

       FieldTagListFormatter -> list [label="Inherits from", arrowhead=empty];
       FieldTagListFormatter -> parse_tags [label="Uses", arrowhead=vee, style=dashed];
   }

**Key Points**

* **Inheritance:** `FieldTagListFormatter` is a specialized version of the built-in `list` class, adding features tailored for tag management.
* **Data Structure:** Internally, it stores tags as a list (`self.tags`) to maintain their order.
* **Validation:** It enforces data integrity by validating both individual tags and the data structures used to pass multiple tags at once.
* **Flexibility:** It offers various methods for adding, removing, and converting tags, making it adaptable to different use cases within your application.
* **Parser:** It utilizes the `parse_tags` function to handle tag input in a user-friendly way, allowing for comma-separated strings, lists, etc.

