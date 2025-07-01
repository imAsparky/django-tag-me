"""tag-me app custom form charfield."""

# from django.core import validators
from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _

from tag_me.utils.collections import FieldTagListFormatter


class TagMeCharField(CharField):
    """Custom tag-me Charfield Form

    Overrides to_python converting values into a
    :class: FieldTagListFormatter, returning the :method: toCSV() string
    in the format that :class: tag_me.utils.parser.parse_tags expects.
    """

    default_error_messages = {
        "invalid": _("Please enter a valid tag/tags"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formatter = FieldTagListFormatter()

    def to_python(self, value):
        """Return FieldTagListFormatter(value).toCSV() string."""

        self.formatter.clear()  # Ensure we start with an empty list
        self.formatter.add_tags(value)
        return self.formatter.toCSV(
            include_trailing_comma=True,  # Ensures correct tag string parsing
        )
