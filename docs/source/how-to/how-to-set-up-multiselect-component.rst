.. include:: ../../extras.rst.txt
.. highlight:: rst
.. index:: how-to-set-up-multiselect-component ; Index


.. _how-to-set-up-multiselect-component:

=============================
Set-up Multi-Select Component
=============================

|

`x-data`:
=========

This is how you initialize the Alpine component on the div.

.. code-block:: html
   :emphasize-lines: 2

    <div
      x-data="alpineTagMeMultiSelect({selected: {{ values }},
      elementId:'{name}'})"
    >

|

`x-ref`:
========

You'll need this if you  want to access component functions from outside the div.

.. code-block:: html
   :emphasize-lines: 3

   <div
      x-data="alpineTagMeMultiSelect({selected: {{ values }},elementId:'{name}'})"
      x-ref="alpineTagMeMultiSelect"
    >

|

`elementId`:
============

Add an ID to the <select> element you want to transform into this multi-select component.

The elementId property you're passing into your alpineTagMeMultiSelect component serves as a bridge linking your custom select component to a pre-existing <select> element in your HTML. Here's what it does:

Finding the Original Element:  When the component initializes (within the init function), it has this code:


.. code-block:: javascript

    const options = document.getElementById(this.elementId).options;


This line of code uses the elementId (e.g., '{name}') to locate the correct <select> element on your page.

Building the Custom Component: The `alpineTagMeMultiSelect` component then extracts the options from this original <select> element. It uses this data as the basis to construct the custom multi-select component.

.. note::

   The default `elementId` uses the Django select element name passed by the custom widget context.

.. code-block:: html
   :emphasize-lines: 3

    <div
      x-data="alpineTagMeMultiSelect({selected: {{ values }},
      elementId:'{name}'})"
    >

|

Key Points
----------

    Data Source: The elementId points the component to the source of its options and potentially some initial selected values.

    Customization: Your custom component hides the original <select> and replaces it with a new, interactive multi-select element, while using the original data.

|

Why You Might Include It Here
-----------------------------

While you may not be directly interacting with the elementId in the <div> tag where you're using the component, including it ensures these things:

    Consistency: Your component has the information it needs to initialize itself correctly, even if it's not immediately used for an action triggered from that specific <div>.

    Future Flexibility: If in the future you do need to reference your multi-select component and locate its connected <select> element, having the 'elementId' set up makes it easier.


`logging`:
==========

This is a handy function you can add to help debugging. You will need `x-ref` as well.


.. code-block:: html
   :emphasize-lines: 5

   <div
      x-data="alpineTagMeMultiSelect({selected: {{ values }},elementId:'{name}'})"
      x-ref="alpineTagMeMultiSelect"
      @click="$refs.alpineTagMeMultiSelect.logOptions()"
    >
