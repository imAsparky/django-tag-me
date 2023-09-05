"""tag-me app collections."""
from django.core.exceptions import ValidationError
from django.db.models.fields import CharField
from django.utils.translation import gettext_lazy as _

from tag_me.db.forms.fields import TagMeCharFieldForm
from tag_me.utils.collections import FieldTagListFormatter

null_tags: list = [
    "null",
    "Null",
    "NULL",
]


class TagMeCharField(CharField):
    """A tagged field inheriting from Charfield."""

    def to_python(self, value):
        """
        Convert the input value into the expected Python data type, raising
        django.core.exceptions.ValidationError if the data can't be converted.
        Return the converted value. Subclasses should override this.
        """

        match value:
            case dict():
                # If there is a "tags" key, parse the "tags" list to
                # FieldTagList  ensures that it passes validation.
                if "tags" in value.keys():
                    parsed_tags = FieldTagListFormatter(value["tags"])

                    value = parsed_tags.toCSV()

                # If the value does not contain a 'tags' key, return the value
                # so its checked in validation.
                return value

            case list():
                for tag in null_tags:
                    if tag in value:
                        value = value.replace(tag, "")

                parsed_tags = FieldTagListFormatter(value)

                value = parsed_tags.toCSV()

            case set():
                value = list(value)

                for tag in null_tags:
                    if tag in value:
                        value = value.replace(tag, "")

                parsed_tags = FieldTagListFormatter(list(value))

                value = parsed_tags.toCSV()

            case str():
                for tag in null_tags:
                    if tag in value:
                        value = value.replace(tag, "")

                parsed_tags = FieldTagListFormatter(value)

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
