"""django-tag-me application configuration."""

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

# Default values for all tag-me settings.
# Consumers can override any of these in their Django settings module.
TAG_ME_SETTING_DEFAULTS = {
    # -------------------------------------------------------------------------
    # Default user tag seeding
    #
    # When enabled, tag-me loads default tags from a JSON file and applies
    # them to newly created TaggedFieldModel records during migration.
    #
    # DJ_TAG_ME_DEFAULT_TAGS_FILE:
    #   Path to the JSON file containing default user tags. Relative paths
    #   resolve against the working directory. Defaults to
    #   "default_user_tags.json" in the project root.
    #
    # DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS:
    #   Load defaults only when a TaggedFieldModel is first created
    #   (typically during initial migration). Does not overwrite existing tags.
    #
    # DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG:
    #   Force-load defaults on EVERY migration. Useful for development/testing
    #   to reset tags to known state. Will overwrite user changes.
    # -------------------------------------------------------------------------
    "DJ_TAG_ME_DEFAULT_TAGS_FILE": "default_user_tags.json",
    "DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS": False,
    "DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG": False,
    # -------------------------------------------------------------------------
    # UI configuration
    # -------------------------------------------------------------------------
    "DJ_TAG_ME_TEMPLATES": {
        "default": "tag_me/tag_me_select.html",
    },
    "DJ_TAG_ME_MAX_NUMBER_DISPLAYED": 2,
    "DJ_TAG_ME_URLS": {
        "help_url": "",
        "mgmt_url": "",
    },
}


class DjangoTagMeConfig(AppConfig):
    """Django tag-me application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tag_me"
    verbose_name = _("Django Tag Me")
    verbose_name_plural = _("Django Tag Me")

    def ready(self):
        super().ready()
        self._initialize_settings()
        self._connect_signals()

    def _initialize_settings(self):
        """
        Set default values for any tag-me settings not already defined
        by the consumer's Django settings module.
        """
        for setting_name, default_value in TAG_ME_SETTING_DEFAULTS.items():
            if not hasattr(settings, setting_name):
                setattr(settings, setting_name, default_value)

    def _connect_signals(self):
        """Connect signal handlers for post-migration processing."""
        from tag_me.registry import post_migrate_handler

        post_migrate.connect(post_migrate_handler)
