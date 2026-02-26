"""\
Registry Module

SystemTagRegistry

This module provides a singleton registry for managing system tags in Django models.
It handles the registration and population of TaggedFieldModel records for fields
using the TagMeCharField, ensuring proper initialization after database migrations.

The registry collects field metadata during model class creation and populates
the database only after all migrations are complete, solving the chicken-and-egg
problem of needing to access tables that might not exist during model initialization.

Usage:
   The registry is primarily used internally by TagMeCharField's contribute_to_class
   method and should not need to be accessed directly in most cases.

Implementation Notes:
   - Uses singleton pattern to ensure single registry instance
   - Defers database operations until after migrations
   - Thread-safe field registration
   - Handles synchronization of related fields
   - Clears ContentType cache before field registration to handle RenameModel
   - Runs orphan merger after field registration to handle DeleteModel+CreateModel

Signal Handling:
   Django's migrate command runs ALL migrations first, then emits post_migrate
   once per installed app in a batch at the end. Since all tables already exist
   by the time any post_migrate fires, we simply run on the first signal and
   skip subsequent ones using a run-once flag.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set

import structlog
from django.conf import settings
from django.db import (
    models,
    transaction,
)
from django.db import (
    utils as django_db_exceptions,
)

logger = structlog.get_logger(__name__)


class TagType(Enum):
    SYSTEM = "system"
    USER = "user"


@dataclass(frozen=True)
class FieldMetadata:
    model: models.Model
    field_name: str
    tags: str
    model_name: str
    model_verbose_name: str
    field_verbose_name: str
    tag_type: TagType


class TagPersistence:
    """\
    Manages the persistence of tag fields and their default values in the Django database.

    This class handles loading default user tags from a JSON file and saving field metadata
    to the database. It supports both system and user-defined tags, with different handling
    for each type.

    IMPORTANT: Lookups use ContentType FK + field_name only. The model_name field is
    stored for display/caching purposes but is NOT used in lookups to ensure resilience
    to model renames.

    Attributes:
        default_user_tags (Dict): A dictionary containing default tags for user-defined fields.
            The dictionary keys are field names and values are strings containing the field's
            default tags.
    """

    def __init__(self):
        """\
        Initializes the TagPersistence instance.

        If SEED_INITIAL_USER_DEFAULT_TAGS setting is True, attempts to load default user tags
        from the configured tags file (DJ_TAG_ME_DEFAULT_TAGS_FILE setting, defaults to
        "default_user_tags.json" in the project root).
        """
        self.default_user_tags: Dict = {}
        if (
            settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS
            or settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG
        ):
            self._load_default_user_tags()

    def _load_default_user_tags(self) -> None:
        """\
        Loads default user tags from the configured JSON file.

        The file path is read from the DJ_TAG_ME_DEFAULT_TAGS_FILE setting,
        falling back to "default_user_tags.json" if not set. Relative paths
        resolve against the current working directory.

        The JSON file should contain a dictionary mapping field names to
        comma-separated strings, where each string contains default tags.

        Example JSON format:
            {
                "field_name": ["Field Label", "tag1,tag2,tag3,"]
            }

        Any errors during file loading (file not found, invalid JSON, permission issues) are
        logged but do not raise exceptions, leaving default_user_tags empty.
        """
        tags_path = getattr(
            settings,
            "DJ_TAG_ME_DEFAULT_TAGS_FILE",
            "default_user_tags.json",
        )
        try:
            with open(tags_path, "r") as f:
                self.default_user_tags = json.load(f)
                logger.debug(
                    "default_user_tags_loaded",
                    field_count=len(self.default_user_tags),
                    path=str(tags_path),
                )
        except FileNotFoundError:
            logger.warning("default_user_tags_file_not_found", path=str(tags_path))
        except (json.JSONDecodeError, PermissionError, IOError):
            logger.exception("default_user_tags_read_error", path=str(tags_path))

    def save_fields(self, metadata: set[FieldMetadata]) -> None:
        """\
        Saves field metadata to the database and sets up tag synchronization.

        Creates or updates TaggedFieldModel instances for each field in the metadata set.

        IMPORTANT: Uses update_or_create with content + field_name as the lookup keys.
        The model_name, model_verbose_name, and field_verbose_name are stored in defaults
        so they get refreshed on each migration (in case the model was renamed).

        For system tags, uses the tags directly from the metadata. For user tags, applies
        default tags from default_user_tags if available and the field is newly created.
        The reason we limit adding the default user tags to created fields is so we dont overwrite
        if the user has made updates.

        Args:
            metadata (set[FieldMetadata]): A set of FieldMetadata instances containing
                the fields to be saved.

        Raises:
            AttributeError: If the model or field attributes are invalid.
            django_db_exceptions.Error: If there's a database transaction error.
            KeyError: If required field data is missing.
            IndexError: If the tag data format is invalid.

        Notes:
            - Uses database transactions to ensure atomicity.
            - Updates field synchronization after saving all fields.
            - Creates a default TagMeSynchronise instance if it doesn't exist.
        """
        # Imports are here to make sure everything is ready first.
        from django.contrib.contenttypes.models import ContentType

        from tag_me.models import (
            TaggedFieldModel,
            TagMeSynchronise,
        )
        from tag_me.utils.tag_mgmt_system import (
            update_fields_that_should_be_synchronised,
        )

        # Clear ContentType cache to ensure we see any changes
        # made by RenameModel migrations (which use .update() and bypass
        # the in-memory cache). Without this, get_for_model() can create
        # duplicate ContentType records after a model rename.
        ContentType.objects.clear_cache()

        for field in metadata:
            try:
                with transaction.atomic():
                    content_type = ContentType.objects.get_for_model(field.model)

                    # Use update_or_create instead of get_or_create
                    # Lookup is by content + field_name only (stable across renames)
                    # The defaults dict contains display fields that may change
                    tagged_field, created = TaggedFieldModel.objects.update_or_create(
                        content=content_type,
                        field_name=field.field_name,
                        defaults={
                            # These fields are refreshed on every migration to stay current
                            # They're for display/caching only, not for lookups
                            "model_name": field.model_name,
                            "model_verbose_name": field.model_verbose_name,
                            "field_verbose_name": field.field_verbose_name,
                            "tag_type": field.tag_type.value,
                        },
                    )

                    if field.tag_type == TagType.SYSTEM:
                        tagged_field.default_tags = field.tags
                    elif field.tag_type == TagType.USER and (
                        created
                        or settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG
                    ):
                        # Walrus operator (:=) assigns and tests in one step
                        # Equivalent to:
                        # field_tags = self.default_user_tags.get(metadata.field_name)
                        # if field_tags:
                        if field_tags := self.default_user_tags.get(field.field_name):
                            tagged_field.default_tags = field_tags[1]

                    tagged_field.save()

                    action = "created" if created else "updated"
                    logger.info(
                        "tagged_field_saved",
                        action=action,
                        model_name=field.model_name,
                        field_name=field.field_name,
                        tag_type=field.tag_type.value,
                    )

            except AttributeError:
                logger.exception(
                    "tagged_field_save_failed",
                    field_name=field.field_name,
                    reason="invalid_attributes",
                )
                raise
            except (django_db_exceptions.Error,):
                logger.exception(
                    "tagged_field_save_failed",
                    field_name=field.field_name,
                    reason="database_error",
                )
                raise
            except KeyError:
                logger.exception(
                    "tagged_field_save_failed",
                    field_name=field.field_name,
                    reason="missing_field_data",
                )
                raise
            except IndexError:
                logger.exception(
                    "tagged_field_save_failed",
                    field_name=field.field_name,
                    reason="invalid_tag_format",
                )
                raise

        update_fields_that_should_be_synchronised()

        sync, _ = TagMeSynchronise.objects.get_or_create(name="default")
        sync.check_field_sync_list_lengths()


class SystemTagRegistry:
    """\
    A singleton registry for managing system tag fields in Django models.

    This registry collects field metadata during model class creation and handles
    the population of TaggedFieldModel records after all migrations are complete.
    It uses a singleton pattern to ensure a single registry instance exists.

    Attributes:
        _instance (SystemTagRegistry): The singleton instance of the registry.
        _fields (Set[FieldMetadata]): A set containing metadata for all registered fields.
        _is_ready (bool): Flag indicating whether the registry is ready for field population.
        _has_populated (bool): Flag to ensure population runs only once per process.
    """

    _instance = None
    _fields: Set[FieldMetadata] = set()
    _is_ready: bool = False
    _has_populated: bool = False

    @classmethod
    def register_field(
        cls,
        model: models.Model,
        field_name: str,
        tags: str,
        model_name: str,
        model_verbose_name: str,
        field_verbose_name: str,
        tag_type: str,
    ) -> None:
        """\
        Registers a field with the system tag registry.

        Creates a FieldMetadata instance for the field and adds it to the registry.
        Initializes the registry singleton if it doesn't exist.

        Args:
            model (models.Model): The Django model class containing the field.
            field_name (str): Name of the field being registered.
            tags (str): Comma-separated string of default tags for the field.
            model_name (str): The name of the model.
            model_verbose_name (str): Human-readable name of the model.
            field_verbose_name (str): Human-readable name of the field.
            tag_type (str): Type of the tag field ('system' or 'user').
        """
        if cls._instance is None:
            cls._instance = cls()

        metadata = FieldMetadata(
            model=model,
            field_name=field_name,
            tags=tags,
            model_name=model_name,
            model_verbose_name=model_verbose_name,
            field_verbose_name=field_verbose_name,
            tag_type=TagType(tag_type.lower()),
        )

        cls._fields.add(metadata)

    @classmethod
    def mark_ready(cls) -> None:
        """\
        Marks the registry as ready for field population.

        This method should be called after all migrations are complete
        to indicate that it's safe to populate the registered fields.
        """
        cls._is_ready = True

    @classmethod
    def populate_registered_fields(cls) -> None:
        """
        Populates/updates the database with registered field metadata and tag records.

        Runs once after migrate to ensure:
        - Field metadata (TaggedFieldModel) stays current
        - System tags reflect any choice/field changes
        - New users get their UserTag entries

        Guarded by _has_populated to prevent repeated execution when
        post_migrate fires once per installed app.
        """
        if not cls._is_ready:
            logger.info("registry_not_ready")
            return

        if cls._has_populated:
            return

        cls._has_populated = True

        persistence = TagPersistence()
        persistence.save_fields(cls._fields)

        # Detect and merge orphaned TaggedFieldModel records.
        # This handles the case where Django generates DeleteModel + CreateModel
        # instead of RenameModel, which creates a new ContentType and orphans
        # the old TaggedFieldModel records along with their UserTag/SystemTag FKs.
        from tag_me.utils.orphan_merger import merge_orphaned_tagged_fields

        merge_orphaned_tagged_fields()

        # Populate the actual tag records
        from tag_me.utils.tag_mgmt_system import (
            populate_all_tag_records,
        )

        populate_all_tag_records()

    @classmethod
    def reset(cls):
        """
        Reset registry state.

        Useful for testing to allow populate_registered_fields to run again.
        """
        cls._instance = None
        cls._is_ready = False
        cls._has_populated = False


def post_migrate_handler(sender, **kwargs):
    """
    Signal handler for Django's post_migrate signal.

    Django's migrate command runs all migrations first, then emits
    post_migrate once per installed app in a batch at the end. By the
    time this handler fires, all database tables already exist.

    We run on the first post_migrate signal and skip subsequent ones.
    The dispatch_uid="tag_me_post_migrate" on the signal connection
    prevents duplicate handler registration, and the _has_populated
    guard on SystemTagRegistry prevents duplicate execution.

    Args:
        sender: The AppConfig that triggered the signal
        **kwargs: Additional arguments provided by the signal
    """
    SystemTagRegistry.mark_ready()
    SystemTagRegistry.populate_registered_fields()
