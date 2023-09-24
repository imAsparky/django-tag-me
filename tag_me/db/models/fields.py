"""tag-me app collections."""
from django.core import validators
from django.core.exceptions import ValidationError
from django.db.models.fields import CharField
from django.utils.translation import gettext_lazy as _

from tag_me.db.forms.fields import TagMeCharFieldForm
from tag_me.utils.collections import FieldTagListFormatter


class TagMeCharField(CharField):
    """A tagged field inheriting from Charfield."""

    def __init__(
        self,
        *args,
        choices=None,
        db_collation=None,
        **kwargs,
    ):
        self.choices = choices
        super().__init__(
            *args,
            choices=choices,
            db_collation=db_collation,
            **kwargs,
        )
        self.db_collation = db_collation
        if self.max_length is not None:
            self.validators.append(
                validators.MaxLengthValidator(self.max_length)
            )

    def to_python(self, value):
        """
        Convert the input value into the expected Python data type, raising
        django.core.exceptions.ValidationError if the data can't be converted.
        Return the converted value. Subclasses should override this.
        """

        if self.choices:
            return value

        match value:
            case None:
                value = ""
                return value
            case dict():
                # If there is a "tags" key, parse the "tags" list to
                # FieldTagList  ensures that it passes validation.
                if "tags" in value.keys():
                    parsed_tags = FieldTagListFormatter(value["tags"])

                    value = parsed_tags.toCSV()

                # If the value does not contain a 'tags' key, return the value
                # so its checked in validation.
                return value

            case list() | str() | FieldTagListFormatter():
                parsed_tags = FieldTagListFormatter(value)

                value = parsed_tags.toCSV()

            case set():
                value = list(value)

                parsed_tags = FieldTagListFormatter(list(value))

                value = parsed_tags.toCSV()

            case _:
                raise ValidationError(
                    _("%(value)s is not type str, set, list or dict"),
                    params={"value": value},
                    code="invalid",
                )

        return value

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": TagMeCharFieldForm,
                **kwargs,
            }
        )

    def validate(self, value, model_instance):
        """
        Validate value and raise ValidationError if necessary. Subclasses
        should override this to provide validation logic.
        """

        if not self.editable:
            # Skip validation for non-editable fields.

            return

        if self.choices is not None and value not in self.empty_values:
            for option_key, option_value in self.choices:
                if isinstance(option_value, (list, tuple)):
                    # This is an optgroup, so look inside the group for
                    # options.
                    for optgroup_key, optgroup_value in option_value:
                        if value == optgroup_key:
                            return
                elif value == option_key:
                    return
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        if value is None and not self.null:
            raise ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise ValidationError(self.error_messages["blank"], code="blank")
