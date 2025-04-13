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

from tag_me.models import UserTag
from tag_me.utils.collections import FieldTagListFormatter

User = get_user_model()
logger = logging.getLogger(__name__)


class TagMeSelectMultipleWidget(forms.SelectMultiple):
    multiple = True

    # @override
    def render(self, name, value, attrs=None, renderer=None) -> str:
        """Renders a multiple select HTML element with dynamically generated choices.  # noqa: E501

        A custom Django form widget that provides user-specific options
        tailored to a particular model field. It's designed to be flexible and
        works by fetching relevant tag choices on the fly.

        Args:
            :param name: The name attribute to use for the generated
                         <select> element.
            :param value:  The currently selected value or values for the
                           field.  This can be a single value or potentially a
                           list/iterable of values for multiple selection.
            :param attrs: (dict, optional) A dictionary of additional
                          attributes to include in the rendered <select> tag
                          (e.g., 'id', 'class')
            :param renderer:  (Django Renderer, optional) An advanced option
                                            to override the rendering engine.
                                            Most users can ignore this.

        Returns:
            str:  Mark safe HTML output representing the fully formed <select>
                  element with its <option> tags populated from your dynamic
                  choices.
        """
        # Important: 'attrs' is modified in place by removing some entries
        # The 'attrs' removed are for filtering choices and not required
        # elsewhere.
        # css_class = self.attrs.get("css_class", None)
        self.choices: list = []
        _add_tag_url: str = ""

        _all_tag_fields_mixin: bool = self.attrs.get("all_tag_fields_mixin", False)
        _auto_select_new_tags: bool = self.attrs.get("auto_select_new_tags", True)
        _display_all_tags: bool = self.attrs.get("display_all_tags", False)
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

        _all_tag_fields_tag_string = self.attrs.get("all_tag_fields_tag_string", "")
        _tag_choices: str = self.attrs.get("tag_choices", "")

        user = self.attrs.get("user", None)

        # Call the parent class render (essential for Widget functionality)
        super().render(name, value, attrs, renderer)

        _template = get_template(_template_name)

        _tags_string: str = ""
        try:
            # This will be used to iterate over all tags
            # lists and add a dropdown, eg for use in a search system
            if _all_tag_fields_mixin:
                _tags_string = _all_tag_fields_tag_string
                _permitted_to_add_tags = False

            # This will put all user tags into one dropdown
            elif _display_all_tags:
                user_tags = (
                    UserTag.objects.filter(
                        user=user,
                    )
                    .exclude(tags=None)
                    .distinct()
                )
                tags = FieldTagListFormatter()
                for tag in user_tags:
                    tags.add_tags(tag.tags)
                _tags_string = tags.toCSV(include_trailing_comma=True)
                _permitted_to_add_tags = False

            else:
                if _tag_choices:
                    # Here we are using the choices set in the model charfield.
                    _tags_string = _tag_choices
                    # If its a system tag, ie choices field, users cant modify the tags
                    _permitted_to_add_tags = False
                else:
                    # Dynamically fetch user and field specific choices.
                    user_tags = UserTag.objects.filter(
                        user=user,
                        tagged_field=_tagged_field,
                    ).first()

                    if user_tags.tags:
                        _tags_string = user_tags.tags
                        _add_tag_url = reverse("tag_me:add-tag", args=[user_tags.id])
                    else:
                        self.choices = [""]
        except (AttributeError, UserTag.DoesNotExist):
            logger.exception(msg="Tags Widget Error retrieving tags string")
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
            # "options": json.dumps(options),
        }

        return mark_safe(_template.render(context))
