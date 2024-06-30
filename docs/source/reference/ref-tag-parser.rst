.. highlight:: rst
.. index:: tag-parse ; Index


.. _ref-tag-parser:

==========
Tag Parser
==========


**Overview**

This module provides essential functions for parsing and manipulating tag strings within your Django project. It aims to ensure that tags are handled consistently and safely, adhering to specific formatting rules and avoiding potential security issues:

* **Character Validation:** The core function `is_valid_char` meticulously checks individual characters to ensure they are suitable for inclusion in a tag. It allows alphanumeric characters, standard whitespace, and a few punctuation marks, while excluding control characters and other potentially problematic characters.

* **Control Character Removal:** The `remove_control_chars` function takes a string and strips out any non-printable control characters, ensuring that only valid tag characters remain.

* **Tag Parsing:** The main `parse_tags` function delegates the actual parsing logic to a configurable function (either a custom function defined in settings or a default implementation). This flexibility allows you to tailor the tag parsing behavior to your specific needs. The default `_parse_tags` function handles comma-separated tags, quoted tags (for multi-word tags), and tag normalization.

* **Tag Formatting:** The `edit_string_for_tags` function, similar to `parse_tags`, dynamically selects a function for converting a list of tags into a user-editable string format. This again allows for customization while providing a default implementation (`_edit_string_for_tags`) that follows specific formatting conventions.

**Simplified Diagram (Graphviz)**

.. graphviz::

   digraph {
       rankdir=LR;
       is_valid_char [shape=ellipse, style=filled, fillcolor=lightblue, label="is_valid_char"];
       remove_control_chars [shape=ellipse, style=filled, fillcolor=lightblue, label="remove_control_chars"];
       parse_tags [shape=ellipse, style=filled, fillcolor=lightgreen, label="parse_tags"];
       _parse_tags [shape=ellipse, style=filled, fillcolor=lightgreen, label="_parse_tags (default)"];
       edit_string_for_tags [shape=ellipse, style=filled, fillcolor=lightgreen, label="edit_string_for_tags"];
       _edit_string_for_tags [shape=ellipse, style=filled, fillcolor=lightgreen, label="_edit_string_for_tags (default)"];
       UserTag [shape=box, style=filled, fillcolor=lightyellow, label="UserTag"];

       parse_tags -> _parse_tags [label="Can use (default)", arrowhead=vee, style=dashed];
       edit_string_for_tags -> _edit_string_for_tags [label="Can use (default)", arrowhead=vee, style=dashed];
       remove_control_chars -> is_valid_char [label="Uses", arrowhead=vee];
       _edit_string_for_tags -> UserTag [label="Operates on", arrowhead=vee];
   }

**Key Points**

* **String Manipulation:** The module primarily deals with string manipulation, ensuring that tag strings are correctly formatted and free of invalid characters.
* **Customization:** The `parse_tags` and `edit_string_for_tags` functions provide hooks for custom implementations, allowing you to adapt the parsing and formatting logic as needed.
* **UserTag Interaction:** The `edit_string_for_tags` function interacts with the `UserTag` model, converting tag objects into strings for user editing.


**String parsing to tags examples**

================================= ============================================ ===============================================
Tag input string                  Resulting tags                               Notes
================================= ============================================ ===============================================
django htmx alpinejs              ``["django", "htmx", "alpinejs"]``           No commas, so space delimited
django, htmx alpinejs             ``["django", "htmx alpinejs"]``              Comma present, so comma delimited
"django, htmx" alpinejs tailwind  ``["django, htmx", "alpinejs", "tailwind"]`` All commas are quoted, so space delimited
"django, htmx", alpinejs tailwind ``["django, htmx", "alpinejs tailwind"]``    Contains an unquoted comma, so comma delimited
django "htmx alpinejs" tailwind   ``["django", "htmx alpinejs", "tailwind"]``  No commas, so space delimited
"django" "htmx tailwind           ``["django", "htmx", "tailwind"]``           Unclosed double quote is ignored
================================= ============================================ ===============================================


