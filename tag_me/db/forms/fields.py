"""tag-me FOrm Fields"""
import logging

from django.core import validators
from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _

from tag_me.utils.collections import FieldTagListFormatter

logger = logging.getLogger(__name__)


class TagMeCharFieldForm(CharField):
    default_error_messages = {
        "invalid": _("Please enter a valid tag/tags"),
    }

    def __init__(
        self,
        *,
        max_length=None,
        min_length=None,
        strip=True,
        empty_value="",
        **kwargs,
    ):
        self.max_length = max_length
        self.min_length = min_length
        self.strip = strip
        self.empty_value = empty_value
        super().__init__(**kwargs)
        if min_length is not None:
            self.validators.append(
                validators.MinLengthValidator(int(min_length))
            )
        if max_length is not None:
            self.validators.append(
                validators.MaxLengthValidator(int(max_length))
            )
        self.validators.append(validators.ProhibitNullCharactersValidator())

    def to_python(self, value):
        """This function determines how `value` is stored in the DB."""
        # print(f"#300 TaggedFieldJSONField form func to_python {type(value)}")

        if self.disabled:
            # print(f"#302 TaggedFieldJSONField form disabled {self.disabled}")
            return value
        if value in self.empty_values:
            # print(f"#305 TaggedFieldJSONField form empty values {value}")
            return None

        match value:
            case str():
                # In some cases Django automatically adds a null into the field
                # if its empty.
                # If we have nulls we want the tag list to be [] not ["null"]
                # Doing it this way doesnt nuke any legit tags before calling
                # FieldTagList(value)
                null_tags = [
                    "null",
                    "Null",
                    "NULL",
                ]
                for tag in null_tags:
                    # print(f"$$$$ CHECK VALUE {tag} {value}")
                    if tag in value:
                        value = value.replace(tag, "")

                parsed_tags = FieldTagListFormatter(value)

                return parsed_tags.toCSV()

            case dict():
                """THIS SHOULD BE IN THE VALIDATOR"""

                if "tags" in value.keys():
                    return value
                else:
                    raise ValidationError(
                        self.error_messages[
                            "Error saving dict to DB: Invalid TaggedFieldJSONField value.  Must contain key 'tags'"  # noqa: E501
                        ],
                        code="invalid",
                        params={"value": value},
                    )
            case _:
                logger.error("Invalid type for tags conversion.")
                # raise ValidationError(
                #     self.error_messages[
                #         "Error saving Tags value to DB:Invalid format."
                #     ],
                #     code="invalid",
                #     params={"value": value},
                # )

                return value
