.. highlight:: rst
.. index:: cstm-mgmt-cmd; Index


.. _ref_cstm-mgmt-cmd: 

==============
Custom Migrate
==============


**Overview:**

This custom command (`Command`) is designed to extend Django's built-in `migrate` command. Its primary purpose is to trigger a specific update process after database migrations have been successfully applied. This update process, executed by the `tags` management command, is responsible for maintaining a registry of models and fields that utilize tagging functionality.

**Key Functionality:**

* **Inheritance:**
    - It inherits from Django's `CoreMigrateCommand`. This gives it all the capabilities of the standard `migrate` command, such as applying migrations and handling database synchronization.
* **Custom `handle` Method:**
    - This method overrides the base `handle` method of `CoreMigrateCommand`.
    - It first calls the parent class's `handle` method using `super().handle(*args, **options)`. This ensures that the standard migration process is executed as usual.
    - It then uses Django's `call_command` function to invoke the `tags` management command.
    - The `tags` command's output is captured in a `StringIO` buffer (`out`). This is useful for testing or logging purposes, but the output is ultimately returned by the `handle` method.

**Simplified Diagram (Graphviz)**

.. graphviz::

  digraph {
    rankdir=LR;
    Command [shape=box, style=filled, fillcolor=lightblue, label="Custom Migrate Command"];
    CoreMigrateCommand [shape=box, style=filled, fillcolor=lightgray, label="CoreMigrateCommand (Django)"];
    tags [shape=ellipse, style=filled, fillcolor=lightgreen, label="tags Management Command"];

    Command -> CoreMigrateCommand [label="Inherits", arrowhead=empty];
    Command -> tags [label="Calls after Migration", arrowhead=vee];
  }

**Key Points:**

* **Automatic Update:** The custom command ensures that the `tags` command is executed automatically after every successful migration. This keeps the registry of tagged fields up-to-date, which is likely essential for the proper functioning of your tagging system.
* **Customization:** You could potentially modify this command to perform other tasks after migrations, such as clearing caches, rebuilding indexes, or triggering other maintenance operations.
* **Output Capture:** The captured output from the `tags` command can be used for debugging, logging, or even displayed to the user if desired.

