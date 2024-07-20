"""django-tag-me Apps file."""

# from typing import override

from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# from django.utils.translation.trans_real import settings


class DjangoTagMeConfig(AppConfig):
    """tag_me App name config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tag_me"
    verbose_name = _("Django Tag Me")
    verbose_name_plural = _("Django Tag Me")

    # @override
    def ready(self):
        super().ready()

        if not hasattr(settings, "PROJECT_APPS"):
            settings.PROJECT_APPS: list = settings.INSTALLED_APPS  # type: ignore[attr-defined]
        if not hasattr(settings, "DJ_TAG_ME_THEMES"):
            settings.DJ_TAG_ME_THEMES = {
                "default": "tag_me/tag_me_select.html",
            }
        if not hasattr(settings, "DJ_TAG_ME_MAX_NUMBER_DISPLAYED"):
            settings.DJ_TAG_ME_MAX_NUMBER_DISPLAYED = 2
