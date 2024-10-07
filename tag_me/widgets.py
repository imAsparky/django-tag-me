"""tag-me app custom form widget."""

import json

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import (
    get_template,
)
from django.urls import reverse
from django.utils.safestring import mark_safe

from tag_me.models import UserTag

User = get_user_model()


class TagMeSelectMultipleWidget(forms.SelectMultiple):
    allow_multiple_selected = True

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
        _add_tag_url = ""
        _permitted_to_add_tags = True

        _allow_multiple_select = self.attrs.pop("allow_multiple_select", True)
        _auto_select_new_tags = self.attrs.pop("auto_select_new_tags", True)
        _display_number_selected = self.attrs.pop(
            "display_number_selected", settings.DJ_TAG_ME_MAX_NUMBER_DISPLAYED
        )
        _field_verbose_name = self.attrs.pop("field_verbose_name", None)
        _tag_choices = self.attrs.pop("tag_choices", None)
        _tagged_field = self.attrs.pop("tagged_field", None)
        _help_url = settings.DJ_TAG_ME_URLS["help_url"]
        _mgmt_url = settings.DJ_TAG_ME_URLS["mgmt_url"]

        _template_name = self.attrs.pop(
            "template", settings.DJ_TAG_ME_TEMPLATES["default"]
        )
        user = self.attrs.pop("user", None)

        # Call the parent class render (essential for Widget functionality)
        super().render(name, value, attrs, renderer)

        _template = get_template(_template_name)

        if _tag_choices:
            # Here we are using the choices set in the model charfield.
            self.choices = _tag_choices
            _permitted_to_add_tags = False
        else:
            # Dynamically fetch user and field specific choices as a list.
            user_tags = UserTag.objects.filter(
                user=user,
                tagged_field=_tagged_field,
            ).first()

            if user_tags.tags:
                self.choices = [tag.strip() for tag in user_tags.tags.split(",")]
            else:
                self.choices = []
            _add_tag_url = reverse("tag_me:add-tag", args=[user_tags.id])

        values: list = []
        match value:
            case str():
                for val in value.rstrip(",").split(","):
                    values.append(val.strip())

        context = {
            "add_tag_url": _add_tag_url,
            "allow_multiple_select": json.dumps(_allow_multiple_select),
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
