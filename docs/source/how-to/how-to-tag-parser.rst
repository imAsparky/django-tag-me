.. include:: ../../extras.rst.txt
.. highlight:: rst
.. index:: how-to-tag-parser ; Index


.. _how-to-tag-parser:

==================
Tags Parser Useage
==================

|

The user has a great deal of options for inputing tags.  See below for `tag`
input options and the resultant tag list.

|

====================== ================================= ================================================
Tag input string       Resulting tags                    Notes
====================== ================================= ================================================
apple ball cat         ``["apple", "ball", "cat"]``      No commas, so space delimited
apple, ball cat        ``["apple", "ball cat"]``         Comma present, so comma delimited
"apple, ball" cat dog  ``["apple, ball", "cat", "dog"]`` All commas are quoted, so space delimited
"apple, ball", cat dog ``["apple, ball", "cat dog"]``    Contains an unquoted comma, so comma delimited
apple "ball cat" dog   ``["apple", "ball cat", "dog"]``  No commas, so space delimited
"apple" "ball dog      ``["apple", "ball", "dog"]``      Unclosed double quote is ignored
====================== ================================= ================================================
