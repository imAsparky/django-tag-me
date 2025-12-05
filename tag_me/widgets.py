"""tag-me app custom form widget."""

import json
import logging

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import (
    get_template,
)
from django.urls import reverse
from django.utils.safestring import mark_safe

from tag_me.assets import (
    get_tag_me_css,
    get_tag_me_js,
)
from tag_me.models import SystemTag, UserTag

User = get_user_model()
logger = logging.getLogger(__name__)


class TagMeSelectMultipleWidget(forms.SelectMultiple):
    multiple = True

    class Media:
        """
        Widget media files.

        Note: These use the Vite manifest to get hashed filenames.
        """

        css = {"all": (get_tag_me_css(),)}
        js = (get_tag_me_js(),)

    def render(self, name, value, attrs=None, renderer=None) -> str:
        """Renders a multiple select HTML element with dynamically generated choices.

        Queries either SystemTag or UserTag based on the field's tag_type to get
        available tags, ensuring all tag data is validated and formatted correctly.

        Args:
            :param name: The name attribute to use for the generated <select> element.
            :param value: The currently selected value or values for the field.
            :param attrs: (dict, optional) Additional attributes for the <select> tag.
            :param renderer: (Django Renderer, optional) Override the rendering engine.

        Returns:
            str: Mark safe HTML output representing the fully formed select element.
        """
        self.choices: list = []
        _add_tag_url: str = ""

        _auto_select_new_tags: bool = self.attrs.get("auto_select_new_tags", True)
        _multiple: bool = self.attrs.get("multiple", True)
        _permitted_to_add_tags: bool = True

        _display_number_selected: int = self.attrs.get(
            "display_number_selected", settings.DJ_TAG_ME_MAX_NUMBER_DISPLAYED
        )
        _help_url: str = settings.DJ_TAG_ME_URLS["help_url"]
        _mgmt_url: str = settings.DJ_TAG_ME_URLS["mgmt_url"]
        _template_name = self.attrs.get(
            "template", settings.DJ_TAG_ME_TEMPLATES["default"]
        )

        _field_verbose_name: str = self.attrs.get("field_verbose_name", "")
        _tagged_field: str = self.attrs.get("tagged_field", "")
        _tag_type: str = self.attrs.get("tag_type", "user")

        user = self.attrs.get("user", None)

        # Call the parent class render (essential for Widget functionality)
        super().render(name, value, attrs, renderer)

        _template = get_template(_template_name)

        _tags_string: str = ""
        try:
            if _tag_type == "system":
                # Query SystemTag for available system tags
                if _tagged_field:
                    system_tag = SystemTag.objects.filter(
                        tagged_field=_tagged_field
                    ).first()

                    if system_tag and system_tag.tags:
                        _tags_string = system_tag.tags
                        # System tags are read-only
                        _permitted_to_add_tags = False

            elif _tag_type == "user":
                # Query UserTag for user's custom tags
                if user and _tagged_field:
                    user_tag = UserTag.objects.filter(
                        user=user,
                        tagged_field=_tagged_field,
                    ).first()

                    if user_tag:
                        _add_tag_url = reverse("tag_me:add-tag", args=[user_tag.id])
                        if user_tag.tags:
                            _tags_string = user_tag.tags
                    else:
                        self.choices = [""]

        except (AttributeError, UserTag.DoesNotExist, SystemTag.DoesNotExist):
            logger.exception(msg="Tags Widget Error retrieving tags")
            self.choices = [""]

        # Generate the tag list with empty first option
        if _tags_string:
            # Add empty string at start to override browser's automatic
            # selection of first option in select elements
            self.choices = [""] + [
                tag.strip() for tag in _tags_string.split(",") if tag.strip()
            ]

        values: list = []
        match value:
            case str():
                for val in value.rstrip(",").split(","):
                    values.append(val.strip())

        context = {
            "add_tag_url": _add_tag_url,
            "multiple": json.dumps(_multiple),
            "auto_select_new_tags": json.dumps(_auto_select_new_tags),
            "choices": self.choices,
            "display_number_selected": _display_number_selected,
            "help_url": _help_url,
            "mgmt_url": _mgmt_url,
            "name": name,
            "permitted_to_add_tags": json.dumps(_permitted_to_add_tags),
            "verbose_name": _field_verbose_name,
            "values": values,
        }

        return mark_safe(_template.render(context))
