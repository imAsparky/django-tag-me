"""Users need to be added to the UserTag table."""

import logging

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import (
    DatabaseError,
    DataError,
    IntegrityError,
    transaction,
)

from tag_me.models import (
    TagBase,
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.utils.helpers import (
    #     get_model_tagged_fields_field_and_verbose,
    #     get_models_with_tagged_fields,
    stdout_with_optional_color,
)

logger = logging.getLogger(__name__)

User = get_user_model()


def generate_user_tag_table_records(
    user=None,
):
    """
    Generates `UserTag` records for users who are not yet present in the table.

    This function automatically creates `UserTag` entries for each combination of:

    * **Existing Users (if no user is provided):** Fetches all users who do not currently have entries in the `UserTag` table.
    * **New User (if a user is provided):**  Creates entries only for the specified `user`.
    * **Tagged Fields:** Retrieves all tagged fields the `TaggedFieldModel`.

    For each user and tagged field combination, a new `UserTag` record is created with:

    * The corresponding user and tagged field.
    * Model and field names (both name and verbose name).
    * A unique slug based on the user's ID.
    * Default empty tags and a comment indicating that tags need to be added.

    The bulk creation of `UserTag` objects is performed within a database transaction to ensure data integrity.

    **Args:**
        user (User, optional): A specific user for whom to generate tags. If not provided, tags will be generated for all users missing from the `UserTag` table.

    **Raises:**
        ValidationError:
            * If a duplicate value is attempted to be created for a field with a unique constraint.
            * If invalid data types are provided for any of the `UserTag` fields.
            * If a general database error occurs during record creation.
    """
    stdout_with_optional_color(
        message="tag-me user tag generation tool is running", color_code=36
    )
    try:
        if user:
            users = [user]
            stdout_with_optional_color(
                message=f"A single user < {user.username} > requires updating",
                color_code=96,
            )
        else:
            # Get all unique users from UserTag
            existing_user_ids = UserTag.objects.values_list(
                "user_id", flat=True
            ).distinct()

            # Get all users who are NOT in existing_user_ids
            users = User.objects.exclude(id__in=existing_user_ids)

        user_count = len(users)
        match user_count:
            case 0:
                stdout_with_optional_color(
                    message="Nothing to do, all users are in the UserTag table!\nExiting user tag table generation tool...",
                    color_code=33,
                )
                return
            case 1:
                stdout_with_optional_color(
                    message=f"Generating UserTag rows for {user_count} user!",
                    color_code=36,
                )
            case _:
                stdout_with_optional_color(
                    message=f"Generating UserTag rows for {user_count} users!",
                    color_code=36,
                )
        tagged_fields = TaggedFieldModel.objects.all()
        user_tags = []
        for user in users:
            for field in tagged_fields:
                user_tags.append(
                    UserTag(
                        user=user,
                        tagged_field=field,
                        model_name=field.model_name,
                        model_verbose_name=field.model_verbose_name,
                        field_name=field.field_name,
                        field_verbose_name=field.field_verbose_name,
                        ui_display_name=field.field_verbose_name,
                        slug=TagBase.slugify(tag=str(user.id)),
                        tags=field.default_tags,
                        comment="Auto generated, please add tags and update/delete this comment",
                    )
                )
            with transaction.atomic():
                # Note: Bulk create UserTag objects, ignoring conflicts due to unique constraints.
                UserTag.objects.bulk_create(user_tags, ignore_conflicts=True)

        stdout_with_optional_color(
            message=f"    SUCCESS: Added {len(user_tags)} user tags rows in to the UserTag table for {len(users)} users!",
            color_code=92,
        )

    except IntegrityError as e:
        # Handle unique constraint violations
        if "duplicate key value violates unique constraint" in str(e):
            # Extract the conflicting value or field(s) if possible
            logger.exception(msg="IntegrityError")
            raise ValidationError(f"Duplicate value found for UserTag: {str(e)}")
        else:
            raise

    except DataError as e:
        # Handle data type mismatches
        msg = f"Invalid data type provided for UserTag: {str(e)}"
        logger.exception(msg="DATA ERROR")
        raise ValidationError(msg)

    except DatabaseError as e:
        # Handle general database errors
        msg = f"Database error during UserTag creation: {str(e)}"
        logger.exception(msg="Database Error")
        raise ValidationError(msg)


def update_fields_that_should_be_synchronised():
    """
    Updates the synchronization configuration to include fields marked for tag synchronization.

    This function scans all models and checks for fields that have the 'synchronise'
    attribute set to True. If found, it updates the 'TagMeSynchronise' model (named 'default')
    to ensure that tags applied to those fields will be synchronised across relevant content types.
    """

    # Retrieve or create the default synchronization configuration
    sync, _ = TagMeSynchronise.objects.get_or_create(name="default")

    # Get a list of unique content IDs from existing TaggedFieldModel instances
    model_content_ids = (
        TaggedFieldModel.objects.all().values_list("content_id", flat=True).distinct()
    )

    # Retrieve ContentType models for further processing
    models_for_sync = ContentType.objects.filter(
        id__in=model_content_ids
    )  # Get models_for_sync from the list of content_id's

    # Flag to track changes to the sync config
    sync_updated: bool = False
    for model in models_for_sync:
        for field in model.model_class()._meta.fields:
            # Check if the field has the 'synchronise' attribute, and it's set
            # to True
            if hasattr(field, "synchronise") and field.synchronise:
                # Ensure the field is registered for synchronization
                if not sync.synchronise.get(field.name, False):
                    sync.synchronise[field.name] = []
                # Add the ContentType ID to the sync list for this field
                if model.id not in sync.synchronise[field.name]:
                    sync.synchronise[field.name].append(model.id)
                    sync_updated = True

    # Save the updated synchronization configuration if changes were made
    if sync_updated:
        sync.save()
        sync.check_field_sync_list_lengths()


# def update_models_with_tagged_fields_table() -> None:
#     """Updates the Tagged Field Models table for managing tagged fields.
#
#     This function helps manage the models and fields in your Django project
#     that use the custom 'TagMeCharField' for tagging.  Specifically, it does
#     the following:
#
#     1. Finds all the models that have fields using 'TagMeCharField'.
#     2. Looks at each 'TagMeCharField' within these models.
#     3. Adds or updates information about each tagged field in the
#         'TaggedFieldModel' table.  This provides a centralized way to see which
#         models and fields use tags.
#
#     """
#     for model in get_models_with_tagged_fields():
#         content = ContentType.objects.get_for_model(model, for_concrete_model=True)
#         model_name = content.model_class().__name__
#         model_verbose_name = content.model_class()._meta.verbose_name
#         for field in get_model_tagged_fields_field_and_verbose(
#             model_name=model_name,
#             return_field_objects_only=True,
#         ):
#             match field:
#                 case None:  # Ignore if specific field name is missing
#                     # We test for None because the first tuple returned is None
#                     pass
#                 case _:
#                     (
#                         obj,
#                         created,
#                     ) = TaggedFieldModel.objects.update_or_create(
#                         content=content,
#                         field_name=field.name,
#                         field_verbose_name=field.verbose_name,
#                         model_name=model_name,
#                         model_verbose_name=model_verbose_name,
#                         tag_type=field.tag_type,
#                     )  # Add or update the database entry
#
#                     match created:
#                         case True:
#                             logger.info(
#                                 f"\n-- Created {obj} : {field}"
#                             )  # Log a new entry
#                         case False:
#                             logger.info(
#                                 f"\n-- Updated {obj} : {field}"
#                             )  # Log an updated entry
#         update_fields_that_should_be_synchronised()
#
