"""Users need to be added to the UserTag table."""

import structlog
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
    SystemTag,
    TagBase,
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.utils.helpers import (
    stdout_with_optional_color,
)

logger = structlog.get_logger(__name__)

User = get_user_model()


def populate_all_tag_records(user=None):
    """
    Orchestrator for populating all tag records (system and user).

    This function coordinates the population of both SystemTag and UserTag records.
    It provides a single entry point for all tag record population needs.

    Args:
        user (User, optional): If provided, only populate that specific user's tags.
                              If None, populate for all users.

    This is the primary function to call from management commands or post-migrate signals.
    """
    stdout_with_optional_color(message="tag-me tag population starting", color_code=36)

    try:
        _populate_system_tags()
        _populate_user_tags(user=user)

        stdout_with_optional_color(
            message="tag-me tag population completed successfully",
            color_code=92,
        )
    except Exception:
        logger.exception("tag_population_failed")
        raise


def _populate_system_tags():
    """
    Populates SystemTag records for all system tag fields.

    Scans all TaggedFieldModel instances where tag_type='system' and creates
    or updates corresponding SystemTag records based on the field's default_tags.

    Uses update_or_create() to ensure SystemTag records reflect any changes
    to field choices. If choices are updated, existing SystemTag records are
    updated accordingly.

    Raises:
        ValidationError: If database errors occur during creation.
    """
    stdout_with_optional_color(message="  Populating system tags...", color_code=36)

    try:
        # Get all system tag fields
        system_tag_fields = TaggedFieldModel.objects.filter(tag_type="system")

        if not system_tag_fields.exists():
            stdout_with_optional_color(
                message="    No system tag fields found",
                color_code=33,
            )
            return

        total_created = 0
        total_updated = 0

        for tagged_field in system_tag_fields:
            if not tagged_field.default_tags:
                continue

            # Create one SystemTag per system tag field with all tags
            _, created = SystemTag.objects.update_or_create(
                tagged_field=tagged_field,
                defaults={
                    "tags": tagged_field.default_tags,
                    "model_name": tagged_field.model_name,
                    "model_verbose_name": tagged_field.model_verbose_name,
                    "field_name": tagged_field.field_name,
                    "field_verbose_name": tagged_field.field_verbose_name,
                    "ui_display_name": tagged_field.field_verbose_name,
                    "slug": TagBase.slugify(tag=tagged_field.field_name),
                    "comment": "Auto generated system tags",
                },
            )

            if created:
                total_created += 1
            else:
                total_updated += 1

        stdout_with_optional_color(
            message=f"    Created {total_created} system tags, updated {total_updated}",
            color_code=92,
        )

        logger.info(
            "system_tags_populated",
            created=total_created,
            updated=total_updated,
        )

    except IntegrityError:
        logger.exception("system_tag_integrity_error")
        raise ValidationError("Duplicate system tag found")

    except DataError:
        logger.exception("system_tag_data_error")
        raise ValidationError("Invalid data type for SystemTag")

    except DatabaseError:
        logger.exception("system_tag_database_error")
        raise ValidationError("Database error during SystemTag population")


def _populate_user_tags(user=None):
    """
    Populates UserTag records for user(s) and user tag fields.

    Creates or updates UserTag entries for each combination of:
    - User (specific user if provided, otherwise all users)
    - Tagged field where tag_type='user'

    For each user/field combination, a UserTag record is created with empty
    tags field (user will populate with their custom tags).

    Args:
        user (User, optional): If provided, only populate for this user.
                              If None, populate for all users without existing entries.

    Raises:
        ValidationError: If database errors occur during creation.
    """
    stdout_with_optional_color(message="  Populating user tags...", color_code=36)

    try:
        if user:
            users = [user]
            stdout_with_optional_color(
                message=f"    Processing user: {user.username}",
                color_code=96,
            )
        else:
            # Get all unique users already in UserTag
            existing_user_ids = UserTag.objects.values_list(
                "user_id", flat=True
            ).distinct()

            # Get all users NOT in existing_user_ids
            users = User.objects.exclude(id__in=existing_user_ids)

            user_count = users.count()
            if user_count == 0:
                stdout_with_optional_color(
                    message="    All users already have tag entries",
                    color_code=33,
                )
                return

            stdout_with_optional_color(
                message=f"    Processing {user_count} new user(s)",
                color_code=36,
            )

        # Get only USER tag fields
        user_tag_fields = TaggedFieldModel.objects.filter(tag_type="user")

        if not user_tag_fields.exists():
            stdout_with_optional_color(
                message="    No user tag fields found",
                color_code=33,
            )
            return

        user_tags = []
        for current_user in users:
            for field in user_tag_fields:
                user_tags.append(
                    UserTag(
                        user=current_user,
                        tagged_field=field,
                        model_name=field.model_name,
                        model_verbose_name=field.model_verbose_name,
                        field_name=field.field_name,
                        field_verbose_name=field.field_verbose_name,
                        ui_display_name=field.field_verbose_name,
                        slug=TagBase.slugify(tag=str(current_user.id)),
                        tags="",  # Empty - user will create custom tags
                        comment="Auto generated user tag collection",
                    )
                )

        # Bulk create with transaction for efficiency
        with transaction.atomic():
            UserTag.objects.bulk_create(user_tags, ignore_conflicts=True)

        stdout_with_optional_color(
            message=f"    Created {len(user_tags)} user tag entries",
            color_code=92,
        )

        logger.info(
            "user_tags_populated",
            user_count=len(users),
            tag_entries_created=len(user_tags),
            targeted_user=str(user.id) if user else None,
        )

    except IntegrityError:
        logger.exception("user_tag_integrity_error")
        raise ValidationError("Duplicate user tag found")

    except DataError:
        logger.exception("user_tag_data_error")
        raise ValidationError("Invalid data type for UserTag")

    except DatabaseError:
        logger.exception("user_tag_database_error")
        raise ValidationError("Database error during UserTag population")


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
        # Get the model class - may be None if model was deleted
        model_class = model.model_class()
        if model_class is None:
            # Model no longer exists (deleted app/model), skip it
            logger.debug(
                "sync_skipped_deleted_model",
                app_label=model.app_label,
                model=model.model,
            )
            continue

        for field in model_class._meta.fields:
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
