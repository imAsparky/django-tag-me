"""tag-me app collections."""

from django.db.models.fields import CharField

from tag_me.db.forms.fields import TagMeCharFieldForm
from tag_me.utils.collections import FieldTagListFormatter


class TagMeCharField(CharField):
    """A tagged field inheriting from Charfield."""

    def __init__(
        self,
        *args,
        choices=None,
        db_collation=None,
        max_length=None,
        **kwargs,
    ):
        self.choices = choices
        self.max_length = max_length
        super().__init__(
            *args,
            choices=choices,
            db_collation=db_collation,
            max_length=max_length,
            **kwargs,
        )

    def to_python(self, value):
        """Custom tag-me Charfield.

        Overrides to_python converting values into a
        :class: FieldTagListFormatter, returning the :method: toCSV() string
        in the format that :class: tag_me.utils.parser.parse_tags expects.
        """

        if self.choices:
            return value

        match value:
            case None:
                value = ""
                return value
            case _:
                value = FieldTagListFormatter(value).toCSV()

        return value

    def formfield(self, **kwargs):
        """Overrides formfield adding custom form_class."""

        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {
            "max_length": self.max_length,
            "form_class": TagMeCharFieldForm,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
