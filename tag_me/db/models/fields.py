"""tag-me app custom model charfield."""

import logging

from django.contrib.admin.widgets import AdminTextInputWidget
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.db import (
    OperationalError,
    ProgrammingError,
)
from django.db.models.fields import CharField

from tag_me.db.forms.fields import TagMeCharField as TagMeCharField_FORM
from tag_me.models import TaggedFieldModel
from tag_me.utils.collections import FieldTagListFormatter
from tag_me.widgets import TagMeSelectMultipleWidget

logger = logging.getLogger(__name__)


class TagMeCharField(CharField):
    """A custom Django model field for storing and managing tags.

    This field extends the built-in CharField and utilizes a
    FieldTagListFormatter instance internally to provide tag validation,
    formatting, and manipulation. Tags are stored in the database sorted, and
     in a comma-separated (CSV)  format.
    """

    def __init__(
        self,
        *args,
        allow_multiple_select: bool = True,
        synchronise: bool = False,
        db_collation=None,
        **kwargs,
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

        if self.max_length is None:
            self.max_length = 255

        self.allow_multiple_select = allow_multiple_select
        self.synchronise = synchronise
        self.db_collation = db_collation
        self.validators.append(validators.MaxLengthValidator(self.max_length))
        self.formatter = FieldTagListFormatter()
        # Used to pass choices as a list to widget attrs.
        self._tag_choices: list = []
        self.tag_type: str = "user"
        if self.choices:
            tag_choices_list = []
            # Convert choice labels to a list.
            for label, _ in self.choices:
                tag_choices_list.append(str(label))
            self.formatter.clear()
            self.formatter.add_tags(tag_choices_list)
            self._tag_choices = self.formatter.toList()
            self.tag_type = "system"
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

        # During initial migrations, database tables may not exist yet.
        # This try-except block gracefully handles database queries before the schema
        # is fully set up, allowing migrations to proceed by providing a temporary
        # placeholder TaggedFieldModel instance when database access fails.
        # We catch both OperationalError (typically raised by SQLite) and
        # ProgrammingError (typically raised by PostgreSQL) to handle different
        # database backends gracefully.
        try:
            tagged_field = TaggedFieldModel.objects.filter(
                content=ContentType.objects.get_for_model(self.model),
                field_name=self.name,
            ).first()
        except (OperationalError, ProgrammingError) as e:
            msg = f"{str(e)}: Please check you have run migrations, if so has the TaggedFieldModel table been deleted from your data base?\nWe have added an UNSAVED Tagged Field type as a placeholder for you django-tag-me display.\nPlease resolve this error before using this feature as unintended consequences may occur!"
            tagged_field = TaggedFieldModel()
            logger.error(msg)

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
                        "allow_multiple_select": self.allow_multiple_select,
                        "tagged_field": tagged_field,
                        "model_verbose_name": model_verbose_name,
                        "field_name": self.name,
                        "field_verbose_name": self.verbose_name,
                        "_tag_choices": self._tag_choices,
                    },
                ),
            }

        return super().formfield(**defaults)
