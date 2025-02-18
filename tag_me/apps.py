"""django-tag-me Apps file."""

# from typing import override

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

from tag_me.registry import post_migrate_handler


class DjangoTagMeConfig(AppConfig):
    """tag_me App name config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tag_me"
    verbose_name = _("Django Tag Me")
    verbose_name_plural = _("Django Tag Me")

    # @override
    def ready(self):
        super().ready()

        # Initialize the setting if not already set
        # NOTE: Must be before the post_migrate_handler connector
        # for correct system tag registration
        if not hasattr(settings, "TAG_ME_SYSTEM_TAGS_POPULATED"):
            settings.TAG_ME_SYSTEM_TAGS_POPULATED = False

        # Helpful for loading default user tags on initial migration, and for
        # dev testing. The file `default_tags.json` must be in root.
        # Use SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG for force adding default user tags
        # when migrating in DEBUG. Helpful for debugging.
        if not hasattr(settings, "SEED_INITIAL_USER_DEFAULT_TAGS"):
            settings.SEED_INITIAL_USER_DEFAULT_TAGS = False
        if not hasattr(settings, "SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG"):
            settings.SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG = True

        if not hasattr(settings, "DJ_TAG_ME_USE_CUSTOM_MIGRATE"):
            settings.DJ_TAG_ME_USE_CUSTOM_MIGRATE: bool = False  # type: ignore[attr-defined]

        if not hasattr(settings, "PROJECT_APPS"):
            settings.PROJECT_APPS: list = settings.INSTALLED_APPS  # type: ignore[attr-defined]
        if not hasattr(settings, "DJ_TAG_ME_TEMPLATES"):
            settings.DJ_TAG_ME_TEMPLATES = {
                "default": "tag_me/tag_me_select.html",
            }
        if not hasattr(settings, "DJ_TAG_ME_MAX_NUMBER_DISPLAYED"):
            settings.DJ_TAG_ME_MAX_NUMBER_DISPLAYED = 2

        if not hasattr(settings, "DJ_TAG_ME_URLS"):
            settings.DJ_TAG_ME_URLS: dict = {  # type: ignore[attr-defined]
                "help_url": "",
                "mgmt_url": "",
            }

        # Track migration completion to correct triggering of tag-me jobs.
        post_migrate.connect(post_migrate_handler)
