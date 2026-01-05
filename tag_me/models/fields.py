"""tag-me app custom model charfield.

UPDATED: Choices handling that doesn't fight Django's machinery.
"""

import logging

from django.contrib.admin.widgets import AdminTextInputWidget
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.db import (
    OperationalError,
    ProgrammingError,
)
from django.db.models.fields import CharField

from tag_me.forms.fields import TagMeCharField as TagMeCharField_FORM
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
        system_tag: bool = False,
        db_collation=None,
        **kwargs,
    ):
        """\
        Initializes the custom TagMeCharField model field.

        Args:
            *args: Positional arguments passed to the parent CharField constructor.
            multiple: Boolean indicating if multiple tags can be selected. Defaults to True.
            synchronise: Boolean indicating whether this field is synchronised with other
                models with the same field name. Defaults to False.
            system_tag: Boolean indicating if this field uses system tags (choices).
                Defaults to False (user-created tags).
            db_collation: Optional database collation setting.
            **kwargs: Additional keyword arguments passed to CharField constructor.

        Raises:
            ValueError: If system_tag and choices are inconsistent.
        """
        self.multiple = multiple
        self.synchronise = synchronise
        self.system_tag = system_tag

        # Intercept choices BEFORE passing to parent - we handle it ourselves.
        # This avoids fighting Django's choices machinery.
        self._tag_choices_input = kwargs.pop("choices", None)

        # Validate: empty choices list is not allowed
        if self._tag_choices_input is not None and len(self._tag_choices_input) == 0:
            raise ValueError(
                "TagMeCharField: 'choices' cannot be an empty list. "
                "Provide at least one choice or omit 'choices' entirely for user tags."
            )

        # Validate system_tag and choices consistency BEFORE calling super()
        if self.system_tag and not self._tag_choices_input:
            raise ValueError(
                "system_tag=True requires 'choices' to be provided. "
                "System tags must have predefined choices."
            )

        if not self.system_tag and self._tag_choices_input:
            # DEPRECATION: In future versions, this will be an error.
            # For now, auto-fix and warn to give users time to update.
            import warnings

            warnings.warn(
                "TagMeCharField: Providing 'choices' without system_tag=True is deprecated. "
                "In the next major version, this will raise an error. "
                "Please update your field definition to: "
                "TagMeCharField(choices=..., system_tag=True)",
                DeprecationWarning,
                stacklevel=2,
            )
            self.system_tag = True  # Auto-fix for backwards compatibility

        # Pass to parent WITHOUT choices - we handle choices ourselves
        super().__init__(*args, db_collation=db_collation, **kwargs)

        if self.max_length is None:
            self.max_length = 255
        self.validators.append(validators.MaxLengthValidator(self.max_length))

        # Used to pass choices as a list to widget attrs.
        self._tag_choices: str = ""
        self.tag_type: str = "user"

        # Process our intercepted choices
        if self._tag_choices_input:
            tag_choices_list = []

            match self._tag_choices_input:
                case list() if all(
                    isinstance(x, tuple) and len(x) == 2
                    for x in self._tag_choices_input
                ):
                    # Django choices tuples: [("value", "label"), ...]
                    for value, _ in self._tag_choices_input:
                        tag_choices_list.append(str(value))
                case list():
                    # Simple list: ["tag1", "tag2", ...]
                    tag_choices_list.extend(self._tag_choices_input)
                case _:
                    msg = f"Tag choices must be of type <list> or <model.TextChoices> not {type(self._tag_choices_input)}"
                    logger.error(msg=msg)

            # Use local formatter for initialization only
            # Note: We don't store formatter on self because field instances
            # are shared across threads - see from_db_value, get_prep_value, to_python
            formatter = FieldTagListFormatter()
            formatter.add_tags(tag_choices_list)
            self._tag_choices = formatter.toCSV(include_trailing_comma=True)
            self.tag_type = "system"

    def deconstruct(self):
        """\
        Return a 4-tuple for migrations: (name, path, args, kwargs).

        Only includes kwargs that differ from the field's defaults to keep
        migrations clean and minimal.
        """
        name, path, args, kwargs = super().deconstruct()

        # Include our intercepted choices if present
        if self._tag_choices_input is not None:
            kwargs["choices"] = self._tag_choices_input

        # Only include custom attributes if they differ from defaults
        if self.multiple is not True:
            kwargs["multiple"] = self.multiple
        if self.synchronise is not False:
            kwargs["synchronise"] = self.synchronise
        if self.system_tag is not False:
            kwargs["system_tag"] = self.system_tag

        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        """\
        Converts the database representation of tags into a FieldTagListFormatter compliant format.

        :param value: The raw tag data as retrieved from the database
                            (expected to be a CSV string).
        :param expression: Information about how the value was obtained
                            (e.g., aggregations).
        :param connection: The database connection used.

        :return: A FieldTagListFormatter instance containing the parsed tags.
        """
        # Create a new formatter instance for thread safety
        # Field instances are shared across threads, so we can't use self.formatter
        formatter = FieldTagListFormatter()
        formatter.add_tags(value)

        return formatter.toCSV(
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
        # Create a new formatter instance for thread safety
        formatter = FieldTagListFormatter()
        formatter.add_tags(value)

        return formatter.toCSV(
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
        # Create a new formatter instance for thread safety
        formatter = FieldTagListFormatter()
        formatter.add_tags(value)

        return formatter.toCSV(
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
        """
        super().contribute_to_class(cls, name, **kwargs)

        if not cls._meta.abstract and not cls.__module__.startswith("__fake__"):
            # Convert verbose_name values to strings to handle lazy translation objects
            # This ensures proper serialization and comparison
            model_verbose = cls._meta.verbose_name
            field_verbose = self.verbose_name

            SystemTagRegistry.register_field(
                model=cls,
                field_name=name,
                tags=self._tag_choices,
                model_name=cls._meta.model_name,
                model_verbose_name=str(model_verbose) if model_verbose else None,
                field_verbose_name=str(field_verbose) if field_verbose else None,
                tag_type=self.tag_type,
            )

    def formfield(self, **kwargs):
        """\
        Overrides the default form field generation for this model field.

        Provides flexibility in selecting the form field widget based on the
        provided 'widget' argument in kwargs. Supports custom widgets as well
        as Django Admin widgets.

        :params **kwargs (dict): Additional keyword arguments that can be used
                                 to further customize the form field.

        :returns django.forms.Field: An instance of a form field appropriate
                                    for representing this model field.
        """
        # Pop widget from kwargs so it doesn't get passed twice
        widget = kwargs.pop("widget", None)

        if hasattr(self, "model"):
            # Convert to string to handle lazy translation objects
            model_verbose_name = str(self.model._meta.verbose_name)
        else:
            model_verbose_name = "** No Model **"

        tagged_field = None
        try:
            if not hasattr(self, "model"):
                raise AttributeError("Field not attached to model yet")
            tagged_field = TaggedFieldModel.objects.filter(
                content=ContentType.objects.get_for_model(self.model),
                field_name=self.name,
            ).first()
        except (OperationalError, ProgrammingError, AttributeError) as e:
            msg = f"{str(e)}: Please check you have run migrations, if so has the TaggedFieldModel table been deleted from your data base?\nWe have added an UNSAVED Tagged Field type as a placeholder for you django-tag-me display.\nPlease resolve this error before using this feature as unintended consequences may occur!"
            logger.error(msg)

        # Ensure we always have a TaggedFieldModel instance (even if unsaved placeholder)
        if tagged_field is None:
            tagged_field = TaggedFieldModel()
            logger.warning(
                f"No TaggedFieldModel found for field '{self.name}' - using placeholder"
            )

        if "django.contrib.admin.widgets" in str(widget):
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
                        "tag_type": self.tag_type,
                    },
                ),
            }

        # Merge any remaining kwargs (help_text, label, validators, etc.)
        defaults.update(kwargs)
        return super().formfield(**defaults)
