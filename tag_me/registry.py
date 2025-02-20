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


MigrationTracker
Migration tracking for managing the population of system tags.

This module provides utilities to track the completion of Django migrations
for specific apps, ensuring that system tag population only occurs after
all required database tables are available.

The module tracks a predefined set of Django apps that are known to have
model migrations, waiting for all of them to complete before triggering
the system tag population process.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set

from django.conf import settings
from django.db import (
    models,
    transaction,
)
from django.db import (
    utils as django_db_exceptions,
)

logger = logging.getLogger(__name__)


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

    Attributes:
        default_user_tags (Dict): A dictionary containing default tags for user-defined fields.
            The dictionary keys are field names and values are strings containing the field's
            default tags.
    """

    def __init__(self):
        """\
        Initializes the TagPersistence instance.

        If SEED_INITIAL_USER_DEFAULT_TAGS setting is True, attempts to load default user tags
        from the default_user_tags.json file.
        """
        self.default_user_tags: Dict = {}
        if (
            settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS
            or settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG
        ):
            self._load_default_user_tags()

    def _load_default_user_tags(self) -> None:
        """\
        Loads default user tags from the default_user_tags.json file.

        The JSON file should contain a dictionary mapping field names to comma-separated strings, where each string
        contains default tags.

        Example JSON format:
            {
                "field_name": "tag1,tag2,tag3,"
            }

        Any errors during file loading (file not found, invalid JSON, permission issues) are
        logged but do not raise exceptions, leaving default_user_tags empty.
        """
        try:
            with open("default_user_tags.json", "r") as f:
                self.default_user_tags = json.load(f)
                logger.debug(
                    f"Loaded default user tags from file: {self.default_user_tags}"
                )
        except FileNotFoundError:
            msg = "Default tags file not found: default_user_tags.json"
            logger.exception(msg)
        except (json.JSONDecodeError, PermissionError, IOError):
            msg = "Error reading default_user_tags.json:"
            logger.exception(msg)

    def save_fields(self, metadata: set[FieldMetadata]) -> None:
        """\
        Saves field metadata to the database and sets up tag synchronization.

        Creates or updates TaggedFieldModel instances for each field in the metadata set.
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

        for field in metadata:
            try:
                with transaction.atomic():
                    content_type = ContentType.objects.get_for_model(field.model)

                    tagged_field, created = TaggedFieldModel.objects.get_or_create(
                        content=content_type,
                        field_name=field.field_name,
                        defaults={
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
                    msg = f"Successfully added tag-me {tagged_field}"
                    logger.info(msg)

            except AttributeError:
                msg = f"Invalid model or field attributes for {field.field_name}:"
                logger.exception(msg)
                raise
            except (django_db_exceptions.Error,):
                msg = f"Database transaction error for {field.field_name}:"
                logger.exception(msg)
                raise
            except KeyError:
                msg = f"Missing required field data for {field.field_name}:"
                logger.exception(msg)
                raise
            except IndexError:
                msg = f"Invalid tag data format for {field.field_name}:"
                logger.exception(msg)
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
        """\
        Populates the database with registered field metadata.

        This method checks if the system tags have already been populated and if
        the registry is ready. If both conditions are met, it creates a TagPersistence
        instance and saves all registered field metadata to the database.

        The method is typically called after migrations are complete and the registry
        is marked as ready. It will skip population if either:
        - DJ_TAG_ME_SYSTEM_TAGS_POPULATED setting is True
        - The registry is not marked as ready
        """
        if settings.DJ_TAG_ME_SYSTEM_TAGS_POPULATED:
            logger.info("Default tag-me tags already populated")
            return

        if not cls._is_ready:
            logger.info("Registry not ready, skipping population")
            return

        persistence = TagPersistence()
        persistence.save_fields(cls._fields)


class MigrationTracker:
    """
    Singleton tracker for monitoring the completion of critical app migrations.

    This class tracks migrations for a specific set of Django apps that are
    known to have models and migrations. It ensures that system tag population
    only occurs after all tracked apps have completed their migrations.

    Attributes:
        _instance: Singleton instance of the tracker
        _migrated_apps: Set of apps that have completed migration
        _tracked_apps: Set of apps that need to complete migration before
                      system tag population can occur
    """

    _instance = None
    _migrated_apps = set()
    _tracked_apps = {
        "admin",
        "auth",
        "contenttypes",
        "forms",
        "sessions",
        "sites",
        "tag_me",
    }

    @classmethod
    def register_migration(cls, app_label):
        """
        Registers the completion of an app's migration.

        Called by the post_migrate signal handler to record that an app
        has completed its migrations. Only tracks apps that are in the
        predefined set of _tracked_apps.

        Args:
            app_label: The label of the app that completed migration
        """
        if cls._instance is None:
            cls._instance = cls()
        if app_label in cls._tracked_apps:
            cls._migrated_apps.add(app_label)

    @classmethod
    def all_apps_migrated(cls):
        return cls._migrated_apps == cls._tracked_apps


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
