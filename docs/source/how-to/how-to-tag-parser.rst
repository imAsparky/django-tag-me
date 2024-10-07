
.. include:: ../extras.rst.txta
.. highlight:: rst
.. index:: how-to-tag-parser ; Index


.. _how-to-tag-parser:

=================
Tags Parser Usage
=================

|

Here are examples of different tag input formats with resulting outputs.

|

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
