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
from tag_me.registry import SystemTagRegistry
from tag_me.utils.collections import FieldTagListFormatter
from tag_me.widgets import TagMeSelectMultipleWidget

logger = logging.getLogger(__name__)


class TagMeCharField(CharField):
    """\
    A custom Django model field for storing and managing tags.

    This field extends the built-in CharField and utilizes a
    FieldTagListFormatter instance internally to provide tag validation,
    formatting, and manipulation. Tags are stored in the database sorted, and
     in a comma-separated (CSV)  format.
    """

    def __init__(
        self,
        *args,
        multiple: bool = True,
        synchronise: bool = False,
        db_collation=None,
        **kwargs,
    ):
        """\
        Initializes the custom TagMeCharField model field.

        This field extends the built-in CharField and utilizes a FieldTagListFormatter
        instance internally to provide tag validation, formatting, and manipulation.
        Tags are stored in the database sorted, and in a comma-separated (CSV) format.

        The field can be configured for single or multiple tag selection, and has
        special handling for system-defined choices that get converted into tags.

        Args:
            *args: Positional arguments passed to the parent CharField constructor.
            multiple: Boolean indicating if multiple tags can be selected. Defaults to True.
            synchronise: Boolean indicating whether this field is synchronised with other
                models with the same field name. Defaults to False.
            db_collation: Optional database collation setting.
            **kwargs: Additional keyword arguments passed to CharField constructor.

        Implementation Notes:
            - Sets a default max_length of 255 if none provided
            - Initializes a FieldTagListFormatter for tag handling
            - Converts Django choices into system tags if provided
            - Disables Django's choice machinery when using system tags
            - System tags are stored in both list (_tag_choices) and CSV (_tags_string) formats

        Choices Processing:
            - Django choice tuples (list of (value, label)): extracts values as tags
            - Simple list: uses items directly as tags
            - Invalid types trigger error logging
        """
        super().__init__(*args, **kwargs)

        if self.max_length is None:
            self.max_length = 255

        self.multiple = multiple
        self.synchronise = synchronise
        self.db_collation = db_collation
        self.validators.append(validators.MaxLengthValidator(self.max_length))
        self.formatter = FieldTagListFormatter()
        # Used to pass choices as a list to widget attrs.
        self._tag_choices: str = ""
        self.tag_type: str = "user"

        if self.choices:
            tag_choices_list = []
            # Convert choices into tags.
            match self.choices:
                case list() if all(
                    isinstance(x, tuple) and len(x) == 2 for x in self.choices
                ):
                    """If we have Django choices tuples, extract the first element."""
                    for label, _ in self.choices:
                        tag_choices_list.append(str(label))
                case list():  # More general case comes after
                    """If we have a list just turn into tags."""
                    tag_choices_list.extend(self.choices)
                case _:
                    msg = f"Tag choices must be of type <list> or <model.TextChoices> not {type(self.choices)}"
                    logger.error(msg=msg)

            self.formatter.clear()
            self.formatter.add_tags(tag_choices_list)
            self._tag_choices = self.formatter.toCSV(include_trailing_comma=True)
            self.tag_type = "system"
            self.choices = None  # Disable Django choices machinery.

    def from_db_value(self, value, expression, connection):
        """\
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
        """\
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
        """\
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

    def contribute_to_class(self, cls, name, **kwargs):
        """\
        Registers the field's metadata with the SystemTagRegistry during model class creation.
        This method is called by Django during the model class creation process, before any
        migrations run but after the model class is fully formed.

        The method specifically:
        1. Calls the parent CharField's contribute_to_class
        2. Filters out abstract models and Django's temporary migration models
        3. Registers the field's metadata for later population in the TaggedFieldModel table

        Args:
            cls: The model class this field is being added to
            name: The name of this field on the model
            **kwargs: Additional keyword arguments passed by Django during model creation

        Implementation Notes:
            - Only concrete (non-abstract) models are registered
            - Temporary migration models (starting with '__fake__') are ignored
            - Registration collects metadata but does not access the database
            - Actual database population happens later via post_migrate signal
            - The collected metadata will be used to create/update TaggedFieldModel records
                after all migrations complete

        Database Fields Registered:
            - model: The model class
            - field_name: The name of this field
            - tags: System tags defined in field's choices
            - model_name: The lowercase model name
            - model_verbose_name: Human-readable model name
            - field_verbose_name: Human-readable field name
            - tag_type: Type of tags (system/user)
        """
        super().contribute_to_class(cls, name, **kwargs)

        if not cls._meta.abstract and not cls.__module__.startswith("__fake__"):
            SystemTagRegistry.register_field(
                model=cls,
                field_name=name,
                tags=self._tag_choices,
                model_name=cls._meta.model_name,
                model_verbose_name=cls._meta.verbose_name,
                field_verbose_name=self.verbose_name,
                tag_type=self.tag_type,
            )

    def formfield(self, **kwargs):
        """\
        Overrides the default form field generation for this model field.

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

        # NOTE:During initial migrations, database tables may not exist yet.
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
                        "multiple": self.multiple,
                        "tagged_field": tagged_field,
                        "model_verbose_name": model_verbose_name,
                        "field_name": self.name,
                        "field_verbose_name": self.verbose_name,
                        "tag_choices": self._tag_choices,
                    },
                ),
            }

        return super().formfield(**defaults)
