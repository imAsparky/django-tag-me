"""tag-me Form Fields"""
import logging

from django.forms.fields import CharField
from django.utils.translation import gettext_lazy as _

from tag_me.utils.collections import FieldTagListFormatter

logger = logging.getLogger(__name__)


class TagMeCharFieldForm(CharField):
    """Custom tag-me Charfield Form

    Overrides to_python converting values into a
    :class: FieldTagListFormatter, returning the :method: toCSV() string
    in the format that :class: tag_me.utils.parser.parse_tags expects.
    """

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
        super().__init__(
            max_length=max_length,
            min_length=min_length,
            strip=strip,
            empty_value=empty_value,
            **kwargs,
        )

    def to_python(self, value):
        """Return FieldTagListFormatter(value).toCSV() string."""
        if value not in self.empty_values:
            value = FieldTagListFormatter(value).toCSV()
            if self.strip:
                value = value.strip()
        if value in self.empty_values:
            return self.empty_value
        return value
