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

        # Initialize the system setting global flag
        # NOTE: This setting MUST be before the post_migrate_handler connector
        # for correct system tag registration
        if not hasattr(settings, "DJ_TAG_ME_SYSTEM_TAGS_POPULATED"):
            settings.DJ_TAG_ME_SYSTEM_TAGS_POPULATED = False

        # === CSS Manifest Configuration ===
        # These settings allow tag-me to use your main project's CSS
        # instead of tag-me's own CSS file.

        if not hasattr(settings, "TAGME_CSS_MANIFEST_PATH"):
            # Default: Use tag-me's own CSS manifest
            # Override this to use your project's manifest:
            #   TAGME_CSS_MANIFEST_PATH = 'static/.vite/manifest.json'
            settings.TAGME_CSS_MANIFEST_PATH = None

        if not hasattr(settings, "TAGME_CSS_MANIFEST_KEY"):
            # Default: Look for 'style.css' entry in manifest
            # Override if your CSS uses a different key:
            #   TAGME_CSS_MANIFEST_KEY = 'src/css/main.css'
            settings.TAGME_CSS_MANIFEST_KEY = "style.css"

        if not hasattr(settings, "TAGME_CSS_BASE_PATH"):
            # Default: Tag-me's CSS is in 'tag_me/dist/'
            # Override when using your project's CSS:
            #   TAGME_CSS_BASE_PATH = 'dist'  # or 'static/dist', etc.
            settings.TAGME_CSS_BASE_PATH = "tag_me/dist"

        if not hasattr(settings, "TAGME_CSS_FALLBACK"):
            # Default: Fallback CSS path for development (when no manifest exists)
            # Override for your project:
            #   TAGME_CSS_FALLBACK = 'css/main.css'
            settings.TAGME_CSS_FALLBACK = "tag_me/dist/css/tag-me*.css"

        # These settings are useful for loading default user tags during the initial migration
        # and for development/testing purposes. To use this:
        #
        # 1. Ensure the file `default_user_tags.json` is located in the project's root directory.
        # 2. To force the addition of default user tags during migration in DEBUG mode,
        #    set the environment variable `DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG`.
        # NOTE: Will only load when the TaggedFieldModel record is created, typically ininitial migration
        if not hasattr(settings, "DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS"):
            settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS = False
        # NOTE: Will force the addition of default user tags on each migration.
        if not hasattr(settings, "DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG"):
            settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG = False

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
