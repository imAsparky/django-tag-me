"""tests Apps file."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppNameConfig(AppConfig):
    """tests App name config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests"
    verbose_name = _("Tests")
    verbose_name_plural = _("Tests")
