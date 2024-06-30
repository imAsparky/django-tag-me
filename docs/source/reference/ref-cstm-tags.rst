.. highlight:: rst
.. index:: cstm-tags-cmd; Index


.. _ref_cstm_tags_cmd: 

===============
Custom Tags Cmd
===============

**Overview:**

This `Command` class is a Django management command designed to manage the process of updating the registry of tagged fields (`TaggedFieldModel` table) and checking the configuration for field synchronization (`TagMeSynchronise` model). It essentially automates maintenance tasks related to your tagging system. This called by the custom migrate command.

**Key Functionality:**

* **Inheritance:**
    - It inherits from Django's `BaseCommand`, making it a standard Django management command that can be invoked from the command line.
* **Custom `handle` Method:**
    - This is the core method that gets executed when the command is run. It performs the following steps:
        1. **Logging:** Logs an informational message indicating the start of the update process.
        2. **Table Update:** Calls the `update_models_with_tagged_fields_table` function (imported from `tag_me.utils.helpers`) to update the `TaggedFieldModel` table. This likely involves scanning your Django models to identify fields that use the `TagMeCharField` and updating the registry accordingly.
        3. **Synchronization Check:**  Retrieves (or creates if it doesn't exist) the "default" instance of the `TagMeSynchronise` model. This model stores configuration information about which tagged fields should have their tags synchronized. Then, it calls the `check_field_sync_list_lengths` method on this instance. This method likely performs some validation or analysis of the synchronization configuration and logs relevant messages (warnings or info).
        4. **Error Handling:** Wraps the update process in a `try-except` block to catch any exceptions. If an error occurs, it logs the error with detailed information (`exc_info=True`) and writes an error message to the console using Django's styling (`self.style.ERROR`).
        5. **Success Message:** If no errors occur, it writes a success message to the console using Django's styling (`self.style.SUCCESS`).

**Simplified Diagram (Graphviz)**

.. graphviz::

  digraph {
    rankdir=LR;
    Command [shape=box, style=filled, fillcolor=lightblue, label="Tags Management Command", height=1.5];
    BaseCommand [shape=box, style=filled, fillcolor=lightgray, label="BaseCommand (Django)", height=1.5];
    TaggedFieldModel [shape=box, style=filled, fillcolor=lightcoral, label="TaggedFieldModel"];
    TagMeSynchronise [shape=box, style=filled, fillcolor=lightyellow, label="TagMeSynchronise", height=1.5];
    update_models_with_tagged_fields_table [shape=ellipse, style=filled, fillcolor=lavender, label="update_models_with_tagged_fields_table (helper function)", height=1.5];
    CustomMigrateCommand [shape=box, style=filled, fillcolor=lightgreen, label="Custom Migrate Command"];

    Command -> BaseCommand [label="Inherits", arrowhead=empty];
    Command -> update_models_with_tagged_fields_table [label="Calls", arrowhead=vee];
    update_models_with_tagged_fields_table -> TaggedFieldModel [label="Updates", arrowhead=vee];
    Command -> TagMeSynchronise [label="Checks/Updates", arrowhead=vee];
    CustomMigrateCommand -> Command [label="Calls", arrowhead=vee]; 
  }

**Key Points:**

* **Automation:** The command automates the potentially tedious tasks of updating the tagged field registry and checking synchronization settings, making maintenance easier.
* **Error Handling and Logging:** It includes robust error handling to catch and log exceptions, helping with debugging if something goes wrong.
* **Dependency on Helper Function:** It relies on an external helper function (`update_models_with_tagged_fields_table`) to perform the actual database table update. This promotes code modularity and reusability.
* **Single Responsibility:** The command focuses on a single, well-defined task (updating and checking tag-related configurations), adhering to the Single Responsibility Principle.

