from django import template
from django.apps import apps
from django.utils.translation import pgettext_lazy as _

register = template.Library()


@register.filter
def get_app_verbose_name(content_type):
    try:
        return _(
            "App Verbose Name",
            apps.get_app_config(content_type.app_label).verbose_name,
        )
    except LookupError:
        return _(
            "App Label",
            content_type.app_label,
        )
