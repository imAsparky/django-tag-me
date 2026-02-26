.. include:: ../extras.rst.txt
.. highlight:: rst
.. index:: how-to-management-command ; Index

.. _how-to-management-command:

===============================
How to Use the Tag-me CLI
===============================

Overview
========

Tag-me includes a management command for administration, diagnostics, and
data repair. Most of the time you won't need it — tag-me runs automatically
after every ``migrate``. The CLI exists for when you need to investigate,
fix, or manually trigger tag operations.

.. code-block:: bash

   python manage.py tag_me <action> [options]

|

Built-in Help
=============

Every subcommand has detailed documentation built into the CLI itself.
You don't need to leave the terminal to look things up.

.. code-block:: bash

   # Overview and quick start
   python manage.py tag_me help

   # Detailed help for a specific topic
   python manage.py tag_me help populate
   python manage.py tag_me help check
   python manage.py tag_me help fix-orphans
   python manage.py tag_me help clear-cache
   python manage.py tag_me help rename-workflow
   python manage.py tag_me help troubleshooting

.. tip::

   Start with ``tag_me help`` if you're unsure what to do.
   Start with ``tag_me help troubleshooting`` if something is broken.

|

Common Scenarios
================

|

I Just Renamed a Model
----------------------

When you rename a Django model that uses ``TagMeCharField``, tag-me
automatically detects and repairs the data during ``migrate``. In most
cases, no manual action is needed.

If you want to verify everything is correct:

.. code-block:: bash

   python manage.py tag_me check

If ``check`` reports orphaned records (which can happen if Django generated
``DeleteModel`` + ``CreateModel`` instead of ``RenameModel``):

.. code-block:: bash

   # Preview what will happen
   python manage.py tag_me fix-orphans --dry-run

   # Apply the fix
   python manage.py tag_me fix-orphans

   # Verify
   python manage.py tag_me check

For a full walkthrough of the rename process, including how Django decides
between ``RenameModel`` and ``DeleteModel`` + ``CreateModel``:

.. code-block:: bash

   python manage.py tag_me help rename-workflow

|

I Added a New TagMeCharField
-----------------------------

Tag-me registers new fields automatically when you run ``migrate``.
No manual action is needed.

If you want to verify the field was registered:

.. code-block:: bash

   python manage.py tag_me check --verbose

This shows every registered ``TaggedFieldModel`` with its tag counts.
Your new field should appear in the list.

If it doesn't appear, you can manually trigger registration:

.. code-block:: bash

   python manage.py tag_me populate

|

A New User Has No Tags
----------------------

Tag-me creates ``UserTag`` entries for new users automatically during
``migrate``. If a user was created after the last migration (e.g., via
the admin or a signup form), their tags will be created on the next
``migrate``.

To create tags for a specific user immediately:

.. code-block:: bash

   python manage.py tag_me populate --user <USER_ID>

The user ID can be an integer or a UUID, depending on your user model.

To create tags for all users who are missing them:

.. code-block:: bash

   python manage.py tag_me populate

|

I Changed Choices on a System Tag Field
---------------------------------------

When you update the ``choices`` on a ``TagMeCharField`` with
``system_tag=True``, the new choices are applied automatically during
``migrate``.

To apply changes without running a migration:

.. code-block:: bash

   python manage.py tag_me populate

|

Something Seems Wrong With Tags
--------------------------------

Start with a health check:

.. code-block:: bash

   python manage.py tag_me check

This runs five integrity checks and reports any issues found, along with
the exact command to fix each one.

For a detailed breakdown including per-field tag counts:

.. code-block:: bash

   python manage.py tag_me check --verbose

If you need more guidance:

.. code-block:: bash

   python manage.py tag_me help troubleshooting

|

I Restored a Database Backup
-----------------------------

After restoring a database backup, the ``ContentType`` cache may be stale
and tag records may be out of sync. Run:

.. code-block:: bash

   python manage.py tag_me clear-cache
   python manage.py tag_me populate
   python manage.py tag_me check

|

Subcommand Reference
====================

|

populate
--------

Create or update system and user tag records.

.. code-block:: bash

   python manage.py tag_me populate                # all users
   python manage.py tag_me populate --user 42      # specific user (int)
   python manage.py tag_me populate --user <uuid>  # specific user (UUID)

This is the same operation that runs automatically after every ``migrate``.
It is safe to run repeatedly — existing tags are never overwritten.

|

check
-----

Run a comprehensive data integrity audit. Read-only — no changes are made.

.. code-block:: bash

   python manage.py tag_me check              # summary
   python manage.py tag_me check --verbose    # detailed breakdown

Checks for: orphaned records, stale model names, NULL FK references,
field name mismatches, and stale ContentTypes. Reports the fix command
for each issue found.

|

fix-orphans
-----------

Detect and merge orphaned ``TaggedFieldModel`` records from model renames.

.. code-block:: bash

   python manage.py tag_me fix-orphans --dry-run             # preview
   python manage.py tag_me fix-orphans --dry-run --verbose   # preview + signatures
   python manage.py tag_me fix-orphans                       # apply
   python manage.py tag_me fix-orphans --verbose             # apply + detail

.. warning::

   Always run with ``--dry-run`` first to preview what will happen.

Uses two matching strategies to find the correct merge target:

1. **Unique match** — only one candidate exists with the same app, field
   name, and tag type.
2. **Field signature matching** — when multiple candidates exist (e.g.,
   ``emotions`` is a field on three models), compares the full set of
   tagged field names to find the model with the matching shape.

|

clear-cache
-----------

Clear Django's ``ContentType`` in-memory cache.

.. code-block:: bash

   python manage.py tag_me clear-cache

Rarely needed manually. Tag-me clears the cache automatically during
migrations. Use this after manual database operations or if ``check``
reports stale ContentTypes.

|

help
----

Display built-in documentation.

.. code-block:: bash

   python manage.py tag_me help                    # overview
   python manage.py tag_me help <topic>            # detailed topic

Available topics: ``populate``, ``check``, ``fix-orphans``, ``clear-cache``,
``rename-workflow``, ``troubleshooting``.

|

Automatic vs Manual
===================

Tag-me handles most operations automatically via the ``post_migrate`` signal.
The management command exists for manual intervention and diagnostics.

|

============================== =============== ==========================================
Operation                      Automatic?      When to run manually
============================== =============== ==========================================
Register new fields            ✅ On migrate   Never (unless migrate didn't run)
Update system tag choices      ✅ On migrate   After changing choices without migrating
Create tags for new users      ✅ On migrate   Between migrations, or for a specific user
Merge orphaned records         ✅ On migrate   If auto-merge reports unresolved orphans
Clear ContentType cache        ✅ On migrate   After manual DB operations
Health check                   ❌ Manual       Whenever you want to verify data integrity
============================== =============== ==========================================

|

.. note::

   The old ``populate_tags`` command still works but is deprecated.
   Use ``python manage.py tag_me populate`` instead.
