"""django-tag-me Apps file."""

from django.conf import settings

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppNameConfig(AppConfig):
    """tag_me App name config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tag_me"
    verbose_name = _("Django Tag Me")
    verbose_name_plural = _("Django Tag Me")

    def ready(self):
        if not hasattr(settings, "PROJECT_APPS"):
            settings.PROJECT_APPS: list = settings.INSTALLED_APPS  # type: ignore[attr-defined]
