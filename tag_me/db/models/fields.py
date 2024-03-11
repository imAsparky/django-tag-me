"""tag-me app collections."""

from django.core import validators
from django.db.models.fields import CharField

from tag_me.db.forms.fields import TagMeCharField as TagMeCharField_FORM
from tag_me.widgets import TagMeSelectMultipleWidget
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
        Initializes the custom TagMeCharField model field.

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

        :param value: The raw tag data as retrieved from the database
                            (expected to be a CSV string).
        :param expression: Information about how the value was obtained
                            (e.g., aggregations).
        :param connection: The database connection used.

        :return: A FieldTagListFormatter instance containing the parsed tags.
        """
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
        Converts raw tag data into a structured format suitable for storage.

        This method is responsible for parsing the raw tag data
        (often a string) and converting it into an internal representation that
        can be saved and manipulated by your application.

        :param value: The raw tag data, typically a string.

        :return string: A FieldTagListFormatter.toCSV() formatted string.
        """
        self.formatter.add_tags(value)

        return self.formatter.toCSV()

    def formfield(self, **kwargs):
        """Overrides the default form field generation for this model field.

        This method allows customization of the form field used to represent
        this model field within a Django form.


        :params **kwargs (dict): Additional keyword arguments that can be used
                to further customize the form field.

        :returns django.forms.Field: An instance of a form field appropriate for
                representing this model field.

        """

        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {
            "max_length": self.max_length,
            "form_class": TagMeCharField_FORM,
            "widget": TagMeSelectMultipleWidget(
                    attrs={
                        'model_verbose_name': self.model._meta.verbose_name,
                        'field_name': self.name,
                        'field_verbose_name': self.verbose_name,
                    },

            )
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
