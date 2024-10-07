
.. include:: ../extras.rst.txt
.. highlight:: rst
.. index:: how-to-config ; Index

.. _how-to-config:

=============
How to Config
=============

Overview
========

Some settings can be configured both globally (using Django settings) and 
locally (using attributes in the form widget). In cases where both are 
defined, the widget attribute takes precedence over the global setting.

For example, the ``<setting_name>`` setting can also be configured via the 
``<attribute_name>`` attribute in the form widget. 

This allows for flexible configuration, enabling you to define default 
behavior globally while still allowing for customisation on a per-widget 
basis. 

|

Configuration Options: Global/Local
-----------------------------------

|

===================================== ============================ ===============================================
Setting (in ``settings.py``)          Attribute (in widget)        Notes
===================================== ============================ ===============================================
``DJ_TAG_ME_MAX_NUMBER_DISPLAYED``    ``display_number_selected``  Controls the maximum number of displayed tags
``DJ_TAG_ME_TEMPLATES["default"]``    ``template_name``            Specifies the template for rendering the widget
===================================== ============================ ===============================================

|

Attributes
==========

|

*allow_multiple_select*
-----------------------

**bool**, *optional:*
Whether to allow multiple tags to be selected. ``Defaults to True``.  

|

*auto_select_new_tags*
----------------------

**Not yet implemented**

**bool**, *optional:*
Whether to automatically select newly created tags. ``Defaults to True``.

|

*display_number_selected*
-------------------------

**int**, *optional:*
The maximum number of selected tags to display. Defaults to the value of 
the ``DJ_TAG_ME_MAX_NUMBER_DISPLAYED`` setting.

|

*tagged_field*
--------------

**Not yet implemented**

**str**, *optional:*
The name of the field that will be tagged. ``Defaults to None``.

|

*template_name*
---------------

**str**, *optional:*
The name of the template to use for rendering the widget. Defaults to 
the value of the ``default`` key in the ``DJ_TAG_ME_TEMPLATES`` setting.

|

Settings
========

The ``tag_me`` app comes with sensible defaults, allowing you to start using 
it right out of the box with minimal configuration. However, you can customize 
its behavior using the following settings in your ``settings.py`` file:


|

*DJ_TAG_ME_USE_CUSTOM_MIGRATE*
-------------------------------

**Not Implemented**

**bool**, *optional:*
Whether to use custom migrations for the ``tag_me`` app. ``Defaults to False``.

|

*PROJECT_APPS*
--------------

**list**, *optional:*
This setting allows you to specify a separate list of project-specific 
apps. By default, it uses the value of ``INSTALLED_APPS``.

.. tip::

   **Speed up tag management:**

   To improve the performance of the ``tag_me`` tool, consider splitting your 
   ``INSTALLED_APPS`` into separate lists for project-specific apps and 
   Django's built-in apps. This reduces the number of apps that need to be 
   scanned for ``tag_me`` fields, leading to faster tag management operations.

   **See example below.**

|

.. code-block:: python

      PROJECT_APPS = [
      "app1",
      "app2",
      ]

      DJANGO_APPS = [
      "app3",
      "app4",
      ]

      INSTALLED_APPS: list = []
      INSTALLED_APPS.extend(PROJECT_APPS)
      INSTALLED_APPS.extend(DJANGO_APPS)

|

DJ_TAG_ME_TEMPLATES
-------------------

**dict**, *optional:*
A dictionary of templates used by the ``tag_me`` app. Defaults to:

.. code-block:: python

   {
   "default": "tag_me/tag_me_select.html",
   }

|

DJ_TAG_ME_MAX_NUMBER_DISPLAYED
------------------------------

**int**, *optional:*
The maximum number of selected tags to display in the widget. ``Defaults to 2``.

Once the maximum is reached a ``more`` indicator will show in the widget.

|

DJ_TAG_ME_URLS
--------------

**dict**, *optional:*
A dictionary of urls for tag help and management used by the ``tag_me`` app. Defaults to:

These urls will be used in the searchbar menu. If either/both are supplied they will appear at
the bottom of the menu.

.. code-block:: python

   {
   "help_url": "",
   "mgmt_url": "",
   }

|

.. image:: ../imgs/tag_me_search_menu.png
