"""tag-me app custom model charfield."""

from django.contrib.admin.widgets import AdminTextInputWidget
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

    def __init__(
        self, *args, synchronise: bool = False, db_collation=None, **kwargs
    ):
        """
        Initializes the custom TagMeCharField model field.

        :param synchronise: Boolean indicating whether this field is
            synchronised with other models with the same field name.
        :param *args: Positional arguments passed to the parent CharField
                        constructor.
        :param **kwargs: Keyword arguments passed to the parent CharField
                        constructor.
        """
        super().__init__(*args, **kwargs)
        self.synchronise = synchronise
        self.db_collation = db_collation
        if self.max_length is not None:
            self.validators.append(
                validators.MaxLengthValidator(self.max_length)
            )
        self.formatter = FieldTagListFormatter()
        # Used to pass choices as a list to widget attrs.
        self._tag_choices: list = []
        if self.choices:
            tag_choices_list = []
            # Convert choice labels to a list.
            for label, value in self.choices:
                tag_choices_list.append(str(label))
            self.formatter.clear()
            self.formatter.add_tags(tag_choices_list)
            self._tag_choices = self.formatter.toList()
            self.choices = None  # Disable Django choices machinery.

    def from_db_value(self, value, expression, connection):
        """
        Converts the database representation of tags into a FieldTagListFormatter compliant format. # noqa: E501

        :param value: The raw tag data as retrieved from the database
                            (expected to be a CSV string).
        :param expression: Information about how the value was obtained
                            (e.g., aggregations).
        :param connection: The database connection used.

        :return: A FieldTagListFormatter instance containing the parsed tags.
        """
        self.formatter.clear()  # Ensure we start with an empty list
        self.formatter.add_tags(value)

        return self.formatter.toCSV(
            include_trailing_comma=True,  # Ensures correct tag string parsing
        )

    def get_prep_value(self, value):
        """
        Prepares the tag data for saving into the database.

        :param value: The tag data, either as a FieldTagListFormatter
                        instance or a raw string.

        :return: A CSV-formatted string representing the tags, ready for
                        database storage.
        """
        self.formatter.clear()  # Ensure we start with an empty list
        self.formatter.add_tags(value)

        return self.formatter.toCSV(
            include_trailing_comma=True,  # Ensures correct tag string parsing
        )

    def to_python(self, value):
        """
        Converts raw tag data into a structured format suitable for storage.

        This method is responsible for parsing the raw tag data
        (often a string) and converting it into an internal representation that
        can be saved and manipulated by your application.

        :param value: The raw tag data, typically a string.

        :return string: A FieldTagListFormatter.toCSV() formatted string.
        """
        self.formatter.clear()  # Ensure we start with an empty list
        self.formatter.add_tags(value)

        return self.formatter.toCSV(
            include_trailing_comma=True,  # Ensures correct tag string parsing
        )

    def formfield(self, **kwargs):
        """Overrides the default form field generation for this model field.

        Provides flexibility in selecting the form field widget based on the
        provided 'widget' argument in kwargs. Supports custom widgets as well
        as Django Admin widgets.

        **Context for User/Admin Discrepancies:**

        This customization allows for scenarios where appropriate tag options
        might differ between regular users and admin users. By setting the
        field as readonly in certain contexts, it ensures data consistency and
        prevents the introduction of invalid tags by regular users, while still
        allowing admins to view the full set of selected tags if needed.

        :params **kwargs (dict): Additional keyword arguments that can be used
                                 to further customize the form field.

        :returns django.forms.Field: An instance of a form field appropriate
                                    for representing this model field.
        """

        # Extract and analyze the provided widget
        widget = kwargs.get("widget", None)

        # Added for edge cases when running tests.
        if hasattr(self, "model"):
            model_verbose_name = self.model._meta.verbose_name
        else:
            model_verbose_name = "** No Model **"

        # Conditional widget configuration
        if "django.contrib.admin.widgets" in str(widget):
            # Admin-specific widget setup
            defaults = {
                "max_length": self.max_length,
                "required": False,
                "widget": AdminTextInputWidget(
                    attrs={
                        "readonly": True,
                    },
                ),
            }
        else:
            # Default custom widget setup
            defaults = {
                "form_class": TagMeCharField_FORM,
                "max_length": self.max_length,
                "required": False,
                "widget": TagMeSelectMultipleWidget(
                    attrs={
                        "model_verbose_name": model_verbose_name,
                        "field_name": self.name,
                        "field_verbose_name": self.verbose_name,
                        "_tag_choices": self._tag_choices,
                    },
                ),
            }

        return super().formfield(**defaults)
