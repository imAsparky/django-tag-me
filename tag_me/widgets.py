"""tag-me app custom form widget."""

from typing import override

from django import forms
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from tag_me.utils.helpers import (
    get_user_field_choices_as_list_or_queryset,
)

User = get_user_model()


class TagMeSelectMultipleWidget(forms.SelectMultiple):
    allow_multiple_selected = True
    template_name = "tag_me/tag_me_select.html"

    @override
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
        field_name = self.attrs.pop("field_name", None)
        model_verbose_name = self.attrs.pop("model_verbose_name", None)
        _tag_choices = self.attrs.pop("_tag_choices", None)
        user = self.attrs.pop("user", None)

        # Call the parent class render (essential for Widget functionality)
        super().render(name, value, attrs, renderer)

        if _tag_choices:
            # Here we are using the choices set in the model charfield.
            self.choices = _tag_choices

        else:
            # Dynamically fetch user and field specific choices as a list.
            self.choices = get_user_field_choices_as_list_or_queryset(
                model_verbose_name=model_verbose_name,
                field_name=field_name,
                user=User.objects.get(username=user),
            )

        values: list = []
        match value:
            case str():
                for val in value.rstrip(",").split(","):
                    values.append(val.strip())

        context = {
            "name": name,
            "values": values,
            "choices": self.choices,
            # "options": json.dumps(options),
        }

        return mark_safe(render_to_string(self.template_name, context))


#  -----------  Code for refactor and removal of <select> in html  -----------

# options_list = get_user_field_choices_as_list_tuples(
#     model_verbose_name=model_verbose_name,
#     field_name=field_name,
#     user=User.objects.get(username=user),
# )

# print(f"\n\nWIDGET VALUES: {value}  {type(value)}")
# print(f"\n\nWIDGET CHOICES: {self.choices}  {type(self.choices)}")

# # ... (Code for generating the HTML output, default Django select) ...
# output = [f'<select multiple name="{name}" class={css_class}>']
# for option_value, option_label in self.choices:
#     selected = option_value in value
#     output.append(
#         '<option value="{}" {}>{}</option>'.format(
#             option_value, "selected" if selected else "", option_label
#         )
#     )
# output.append("</select>")

# options: dict = []
# option: dict = {}
# for option in options_list:
#     options.append(
#         {
#             "value": option,
#             "text": option,
#             "search": option,
#             "selected": option in value,
#         }
#     )

# ----------------------------------------------------------------------------

# @override
# def optgroups(self, name, value, attrs=None):
#     """Return a list of optgroups for this widget."""
#     groups = []
#     has_selected = False
#
#     for index, (option_value, option_label) in enumerate(self.choices):
#         if option_value is None:
#             option_value = ""
#
#         subgroup = []
#         if isinstance(option_label, (list, tuple)):
#             group_name = option_value
#             subindex = 0
#             choices = option_label
#         else:
#             group_name = None
#             subindex = None
#             choices = [(option_value, option_label)]
#         groups.append((group_name, subgroup, index))
#
#         for subvalue, sublabel in choices:
#             selected = (
#                 not has_selected or self.allow_multiple_selected
#             ) and str(subvalue) in value[0]
#             has_selected |= selected
#             subgroup.append(
#                 self.create_option(
#                     name,
#                     subvalue,
#                     sublabel,
#                     selected,
#                     index,
#                     subindex=subindex,
#                     attrs=attrs,
#                 )
#             )
#             if subindex is not None:
#                 subindex += 1
#     return groups
