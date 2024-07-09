.. highlight:: rst
.. index:: sync-models ; Index


.. _ref-sync-models:

==============================
The ``TagMeSynchronise`` Model
==============================

The ``TagMeSynchronise`` model is a core component of the django-tag-me library, responsible for managing tag synchronization configuration. It provides the mechanism to automatically propagate tags across related models based on field-level configurations.

**Purpose:**

This model stores the configuration for tag synchronization, indicating which fields in different models should have their tags synchronized automatically.

**Do not interact with this model directly.** When you add or modify ``TagMeCharField`` fields with ``synchronise=True``, the synchronization configuration is automatically updated by the library. To manually refresh the configuration, use the management command:

.. code-block:: bash

    ./manage.py tags -U

**Fields:**

*  **name (CharField):** A unique name for the synchronization configuration (default is "default").
*  **synchronise (JSONField):**  A JSON field storing the mapping of field names to lists of content type IDs that should be synchronized.

**Example `synchronise` Field Data:**

.. code-block:: json

    {
        "topic": ["18", "19"],   // Synchronize tags for fields named "topic" across content types 18 and 19
        "category": ["21"]      // Synchronize tags for fields named "category" on content type 21
    }



**Methods:**

*  **``check_field_sync_list_lengths()``:**
    
    - **Purpose:** Performs a sanity check on the configured synchronization data.
    - **Behavior:**
        1. Iterates through the `synchronise` JSON field, analyzing the length of each field's synchronization list (content type IDs).
        2. Logs warnings for empty or single-entry lists, as these might indicate incomplete configurations or potential errors.
        3. Logs informational messages for lists with two or more entries, differentiating between the minimum required (two) and those with additional entries.
        4. Logs an informational message if there are no fields configured for synchronization.
    - **Returns:** None (only logs messages)



**Internal Methods (not for direct use):**

*  **``_get_field_name_models_to_sync(field)``:**
    - **Purpose:** Retrieves the list of content type IDs associated with a given field name for synchronization.
    - **Arguments:**
        - `field` (str): The name of the field to check for synchronization.
    - **Returns:** 
        - List of content type IDs (strings) if the field is found in the `synchronise` data.
        - ``None`` if the field is not found.

*  **``_add_model_to_sync_list(content_type_id, field)``:**
    - **Purpose:** Adds a content type ID to the synchronization list for a specific field.
    - **Arguments:**
        - `content_type_id` (str): The ID of the content type to add.
        - `field` (str): The name of the field for which synchronization is being configured.
    - **Behavior:**
        1. Validates that both `content_type_id` and `field` are provided.
        2. Checks if the `content_type_id` is already in the list for the given `field`.
        3. If not present, appends the `content_type_id` to the list.
    - **Returns:**
        - ``True`` if the content type was successfully added.
        - ``False`` if either argument was missing or the content type was already in the list.


