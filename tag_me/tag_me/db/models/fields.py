"""tag-me app collections."""

from django.core import validators
from django.db.models.fields import CharField

from tag_me.db.forms.fields import TagMeCharFieldForm
from tag_me.utils.collections import FieldTagListFormatter


class TagMeCharField(CharField):
    """A custom Django model field for storing and managing tags.

    This field extends the built-in CharField and utilizes a
    FieldTagListFormatter instance internally to provide tag validation,
    formatting, and manipulation. Tags are stored in the database sorted, and
     in a comma-separated (CSV)  format.
    """

    def __init__(self, *args, db_collation=None, **kwargs):
        """
        Initializes the TagMeCharField.

        :param *args: Positional arguments passed to the parent CharField constructor. # noqa: E501
        :param **kwargs: Keyword arguments passed to the parent CharField constructor. # noqa: E501
        """
        super().__init__(*args, **kwargs)
        self.db_collation = db_collation
        if self.max_length is not None:
            self.validators.append(
                validators.MaxLengthValidator(self.max_length)
            )
        self.formatter = FieldTagListFormatter()

    def from_db_value(self, value, expression, connection):
        """
        Converts the database representation of tags into a FieldTagListFormatter. # noqa: E501

        :param value: The raw tag data as retrieved from the database (expected to be a CSV string). # noqa: E501
        :param expression: Information about how the value was obtained (e.g., aggregations). # noqa: E501
        :param connection: The database connection used.

        :return: A FieldTagListFormatter instance containing the parsed tags.
        """

        print(f"FIELD MODEL FROM DB VALUE: {value}")
        self.formatter.add_tags(value)
        value = self.formatter.toCSV()

        return value

    def get_prep_value(self, value):
        """
        Prepares the tag data for saving into the database.

        :param value: The tag data, either as a FieldTagListFormatter instance or a raw string. # noqa: E501

        :return: A CSV-formatted string representing the tags, ready for database storage. # noqa: E501
        """
        self.formatter.add_tags(value)
        value = self.formatter.toCSV()

        return value

    def to_python(self, value):
        """
        Converts raw tag input into a FieldTagListFormatter.

        This method is primarily used during form handling to transform input data. # noqa: E501

        :param value: The raw tag data, typically a string.

        :return: A FieldTagListFormatter instance containing the parsed tags.
        """
        print(f"FIELD MODEL TO PYTHON VALUE: {value}")
        self.formatter.add_tags(value)
        value = self.formatter.toCSV()

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
