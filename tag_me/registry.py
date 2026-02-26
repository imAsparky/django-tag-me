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


MigrationTracker
Migration tracking for managing the population of system tags.

This module provides utilities to track the completion of Django migrations
for specific apps, ensuring that system tag population only occurs after
all required database tables are available.

The tracker dynamically builds its tracked app set from INSTALLED_APPS,
filtered to only apps with migrations. This ensures tag-me works regardless
of which Django contrib apps or third-party apps the consumer has installed.
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
    """

    _instance = None
    _fields: Set[FieldMetadata] = set()
    _is_ready: bool = False

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

        Runs after every migrate to ensure:
        - Field metadata (TaggedFieldModel) stays current
        - System tags reflect any choice/field changes
        - New users get their UserTag entries
        """
        if not cls._is_ready:
            logger.info("registry_not_ready")
            return

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


class MigrationTracker:
    """
    Singleton tracker for monitoring the completion of app migrations.

    Dynamically builds the set of tracked apps from INSTALLED_APPS at runtime,
    filtered to only apps that have migrations. This ensures tag-me works
    regardless of which Django contrib apps or third-party apps are installed.

    The tracker waits for ALL installed apps with migrations to complete before
    triggering tag-me's field population, ensuring all database tables exist.

    Attributes:
        _instance: Singleton instance of the tracker
        _migrated_apps: Set of apps that have completed migration
        _tracked_apps: Set of apps to track (built dynamically on first use)
    """

    _instance = None
    _migrated_apps = set()
    _tracked_apps = None  # Built dynamically from INSTALLED_APPS

    @classmethod
    def _get_tracked_apps(cls):
        """
        Build tracked apps from INSTALLED_APPS on first use.

        Only includes apps that have a migrations module (i.e., apps that
        will actually send a post_migrate signal). Apps with
        migrations_module=None have migrations explicitly disabled and
        are excluded.

        Returns:
            set: App labels that need to complete migration before
                 tag-me can safely populate.
        """
        if cls._tracked_apps is not None:
            return cls._tracked_apps

        from django.apps import apps

        cls._tracked_apps = set()
        for app_config in apps.get_app_configs():
            # Only track apps that have a migrations module.
            # Apps with migrations_module=None have migrations disabled
            # and won't send post_migrate, so we must not wait for them.
            migrations_module = getattr(app_config, "migrations_module", None)
            if migrations_module is not None:
                cls._tracked_apps.add(app_config.label)

        logger.debug(
            "migration_tracker_initialized",
            tracked_app_count=len(cls._tracked_apps),
        )

        return cls._tracked_apps

    @classmethod
    def register_migration(cls, app_label):
        """
        Registers the completion of an app's migration.

        Called by the post_migrate signal handler to record that an app
        has completed its migrations. Only tracks apps that are in the
        dynamically built set of tracked apps.

        Args:
            app_label: The label of the app that completed migration
        """
        if cls._instance is None:
            cls._instance = cls()
        tracked = cls._get_tracked_apps()
        if app_label in tracked:
            cls._migrated_apps.add(app_label)

    @classmethod
    def all_apps_migrated(cls):
        """Check if all tracked apps have completed their migrations."""
        return cls._migrated_apps == cls._get_tracked_apps()

    @classmethod
    def reset(cls):
        """
        Reset tracker state. Useful for testing.
        """
        cls._instance = None
        cls._migrated_apps = set()
        cls._tracked_apps = None


def post_migrate_handler(sender, **kwargs):
    """
    Signal handler for Django's post_migrate signal.

    This handler is called after each app completes its migrations. It:
    1. Registers the migration completion with MigrationTracker
    2. Checks if all tracked apps have migrated
    3. If all migrations are complete, marks the SystemTagRegistry as ready
       and triggers the population of system tags

    Args:
        sender: The AppConfig that just completed migration
        **kwargs: Additional arguments provided by the signal
    """
    MigrationTracker.register_migration(sender.label)

    if MigrationTracker.all_apps_migrated():
        from .registry import SystemTagRegistry

        SystemTagRegistry.mark_ready()
        SystemTagRegistry.populate_registered_fields()
