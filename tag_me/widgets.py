"""directory Forms file."""

import logging
from typing import override

from django import forms
from django.utils.safestring import mark_safe

# from tag_me.utils.helpers import get_field_choices

logger = logging.getLogger(__name__)


class TagMeSelectMultipleWidget(forms.SelectMultiple):

    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        # print(f"WIDGET value_from_datadict\n{data}")
        try:
            getter = data.getlist
            print(f"WIDGET GET LIST value_from_datadict\n{name}\n{getter}")
        except AttributeError:
            getter = data.get
        return getter(name)

    def value_omitted_from_data(self, data, files, name):
        print("WIDGET value_omitted_from_data")
        # An unselected <select multiple> doesn't appear in POST data, so it's
        # never known if the value is actually omitted.
        return False

    @override
    def render(self, name, value, attrs=None, renderer=None):
        # ... obtain content_type, field_name, and user ...

        # Pop the choices filters from the attrs dict
        model_verbose_name = self.attrs.pop("model_verbose_name", None)
        field_verbose_name = self.attrs.pop("field_verbose_name", None)
        user = self.attrs.pop("user", None)

        print(f"WIDGET {name} VALUE {self.__dict__}")

        # Fetch choices dynamically
        # choices = get_field_choices(
        #     model_verbose_name=model_verbose_name,
        #     field_verbose_name=field_verbose_name,
        #     user=user,
        # )
        # value = list(value)
        choices = [
            ("tag1", "tag1"),
            ("tag 2", "tag 2"),
            ("tag 3", "tag 3"),
            ("tag4", "tag4"),
        ]

        # Logic to generate HTML, approximately:
        output = ['<select multiple name="{}">'.format(name)]
        for option_value, option_label in choices:
            # print(f"OPTIONS {option_value} -> {option_label}")
            # print(f'OPTION {option_value} == VALUE {value} {option_value == value} ')
            selected = option_value in value  # Assuming values are tag slugs
            # print('WIDGET selected:', selected)
            output.append(
                '<option value="{}" {}>{}</option>'.format(
                    option_value, "selected" if selected else "", option_label
                )
            )
        output.append("</select>")
        # print(f'WIDGET OUTPUT {mark_safe("".join(output))}')
        return mark_safe("".join(output))

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
