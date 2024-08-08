"""tag-me app custom form widget."""

import json
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
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
        css_class = self.attrs.get("css_class", None)
        field_verbose_name = self.attrs.pop("field_verbose_name", None)

        _tag_choices = self.attrs.pop("_tag_choices", None)
        _tagged_field = self.attrs.pop("tagged_field", None)
        user = self.attrs.pop("user", None)

        if "display_number_selected" not in self.attrs:
            self.attrs["display_number_selected"] = (
                settings.DJ_TAG_ME_MAX_NUMBER_DISPLAYED
            )
        # Get the template theme
        if "theme" not in self.attrs:
            self.template_name = settings.DJ_TAG_ME_THEMES["default"]
        else:
            self.template_name = settings.DJ_TAG_ME_THEMES[self.attrs["theme"]]

        add_tag_url = ""
        permitted_to_add_tags = True

        # Call the parent class render (essential for Widget functionality)
        super().render(name, value, attrs, renderer)

        if _tag_choices:
            # Here we are using the choices set in the model charfield.
            self.choices = _tag_choices
            permitted_to_add_tags = False
        else:
            # Dynamically fetch user and field specific choices as a list.
            user_tags = UserTag.objects.filter(
                user=user,
                tagged_field=_tagged_field,
            ).first()

            if user_tags.tags:
                self.choices = [
                    tag.strip() for tag in user_tags.tags.split(",")
                ]
            else:
                self.choices = []
            add_tag_url = reverse("tag_me:add-tag", args=[user_tags.id])

        values: list = []
        match value:
            case str():
                for val in value.rstrip(",").split(","):
                    values.append(val.strip())
        context = {
            "name": name,
            "verbose_name": field_verbose_name,
            "values": values,
            "choices": self.choices,
            # "options": json.dumps(options),
            "display_number_selected": self.attrs["display_number_selected"],
            "permitted_to_add_tags": json.dumps(permitted_to_add_tags),
            "add_tag_url": add_tag_url,
        }

        return mark_safe(render_to_string(self.template_name, context))
