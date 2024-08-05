import logging
import os
import sys


from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models

from tag_me.models import UserTag

User = get_user_model()
logger = logging.getLogger(__name__)


def get_model_tagged_fields_field_and_verbose(
    model_verbose_name: str = "",
    model_name: str = "",
    return_field_objects_only: bool = False,
) -> list[tuple]:
    """Prepares a list of tagged field names and labels for forms.

    This function is specifically useful when you want to create dropdown
    menus (`<select>`) in your Django forms where users can select from
    the tagged fields in your project.

    * Finds models using special tagged fields (likely your custom 'TagMeCharField')
    * Creates a list where each item has:
        * The field's internal name (`field_name`)
        * The field's display label (`field_verbose_name`)

    :param model_verbose_name: (Optional) The display name of a model to filter by.
    :return: A list of tuples ready to be used in forms.
    """
    from tag_me.db.models.fields import TagMeCharField

    _tagged_field_list_choices = [
        (None, None)
    ]  # Placeholder for 'no selection' option
    _field_objects = []
    for model in get_models_with_tagged_fields():
        if (
            model._meta.verbose_name == model_verbose_name
            or model.__name__ == model_name
        ):  # Check if we want this model
            for field in model._meta.fields:
                if issubclass(
                    type(field), TagMeCharField
                ):  # Find our tagged fields
                    label = str(
                        model._meta.get_field(field.name).verbose_name.title()
                    )  # Get a nicely formatted label
                    value = field.name  # Get the field's internal name
                    _tagged_field_list_choices.append(
                        (value, label),
                    )  # Add it to the list
                    _field_objects.append(field)

    if return_field_objects_only:
        return _field_objects

    return _tagged_field_list_choices


def get_models_with_tagged_fields() -> list[models.Model]:
    """Retrieves Django models containing at least one `TagMeCharField` field.

    This function searches through your project's installed apps, filtering out
    models that do not contain any fields of the type `TagMeCharField`.

    The search scope is determined by the ``PROJECT_APPS`` setting. If it's defined,
    only those apps are searched. Otherwise, all apps in ``INSTALLED_APPS`` are considered.

    Returns:
        list[models.Model]: A list of Django model classes that have at least one
            ``TagMeCharField`` field.

    Raises:
        ImportError: If the `tag_me.db.models.fields` module cannot be imported.
    """
    from tag_me.db.models.fields import TagMeCharField

    # Check if the project has a custom list of apps for efficiency
    match settings.PROJECT_APPS:
        case None:
            PROJECT_APPS = settings.INSTALLED_APPS
        case _:
            PROJECT_APPS = settings.PROJECT_APPS

    _tagged_field_models = []  # Stores the models we find
    for app in PROJECT_APPS:
        models = ContentType.objects.filter(
            app_label=app
        )  # Get models from the app

        for model in models:
            for field in model.model_class()._meta.fields:
                if issubclass(
                    type(field), TagMeCharField
                ):  # Check for tagged field
                    _tagged_field_models.append(model.model_class())
                    break  # No need to check other fields in this model

    return _tagged_field_models


def get_models_with_tagged_fields_choices() -> list[tuple]:
    """Prepares a list of model choices for forms with user-friendly labels.

    This function is designed to create dropdown menu options (`<select>`)
    in your Django forms where users can select from models that use tagging.

    * Finds models with special tagged fields using custom'TagMeCharField'
    * Creates a list where each item has:
        * `value`: A machine-readable representation of the model
        * `label`:  The model's display-friendly name (`model_verbose_name`)

    :return: A list of tuples ready to be used in forms to select models.
    """
    from tag_me.db.models.fields import TagMeCharField

    _tagged_field_model_choices = [(None, None)]
    for model in get_models_with_tagged_fields():
        for field in model._meta.fields:
            if issubclass(type(field), TagMeCharField):
                label = model._meta.verbose_name  # User-friendly model name
                value = label
                _tagged_field_model_choices.append(
                    (value, label),
                )
                # return back to the model loop, prevents duplicates in list.
                break

    return _tagged_field_model_choices


def get_model_tagged_fields_choices(
    feature_name: str = "",
) -> list[tuple]:
    """Prepares a list of tagged field options for forms, with optional filtering.

    This function helps create dropdown menus (`<select>`) in your Django forms
    where users can select from tagged fields within your models.

    * Finds models using special tagged fields (likely your custom 'TagMeCharField')
    * Creates a list where each item has:
        * `value`: The field's name (used by the form)
        * `label`:  The field's display-friendly label (`field_verbose_name`)
    * Can optionally filter the results to show tagged fields from a model with a
      specific 'verbose_name'.

    :param feature_name:  (Optional) The 'verbose_name' of a model to filter by.
    :return: A list of tuples ready to be used in forms.
    """
    from tag_me.db.models.fields import TagMeCharField

    if not feature_name:
        feature_name = ""  # Allow filtering by any model

    _tagged_field_list_choices = [
        (None, None)
    ]  # Placeholder for 'no selection' option

    for model in get_models_with_tagged_fields():
        if (
            model._meta.verbose_name == feature_name
        ):  # Check if we want this model
            for field in model._meta.fields:
                if issubclass(
                    type(field), TagMeCharField
                ):  # Find tagged fields
                    label = str(
                        model._meta.get_field(field.name).verbose_name.title()
                    )  # Get a nicely formatted label
                    value = label  # For now, simple label as value
                    _tagged_field_list_choices.append(
                        (value, label),
                    )

    return _tagged_field_list_choices


def get_model_content_type(
    model_verbose_name: str = "",
) -> ContentType | None:
    """Finds the Django ContentType object representing a model.

    This function is useful when you need to interact with Django's internal
    system for tracking content types, especially in relation to your tagged
    fields.

    * Takes the user-friendly display name (`model_verbose_name`) of a model.
    * Searches models with tagged fields (where this is likely relevant).
    * Returns the matching `ContentType` object, which provides metadata about
            the model.

    :param model_verbose_name: The display name of the model you want to find.
    :return: The Django `ContentType` object for the model, or None if not found.
    """

    if not model_verbose_name:
        return None  # Handle the case where no name is provided

    for model in get_models_with_tagged_fields():  # Focus the search
        if model._meta.verbose_name == model_verbose_name:
            content_type = ContentType.objects.get_for_model(
                model=model,
                for_concrete_model=True,  # Ensures we get the right type
            )
            return content_type  # Found it!


def get_user_field_choices_as_list_or_queryset(
    model_verbose_name: str = "",
    field_name: str = "",
    user: User = User,
    return_list: bool = True,
) -> list | models.QuerySet:
    """Fetches tag choices for a specific user, field, and model.

    This function is designed to help you dynamically populate dropdown menus
    or other form elements where users need to select from their own tags.
            Key points:

    * Filters tags based on the provided model name, field name, and user.
    * Returns the result as a Flat List, or optionally a Django QuerySet.

    :param model_verbose_name: The display name of the model the field belongs to.
    :param field_name: The  name of the field.
    :param user: The Django User object representing the user whose tags we want.
    :param return_list: Default return a List, otherwise a Django QuerySet.
    :return: Defaults to a List. optional Django QuerySet representing tag choices.

    """
    choices = UserTag.objects.filter(
        model_verbose_name=model_verbose_name,
        field_name=field_name,
        user=user,
    )

    if return_list:
        return choices.values_list("tags", flat=True)
    else:
        return choices


def get_user_field_choices_as_list_tuples(
    model_verbose_name: str = "",
    field_name: str = "",
    user: User = User,
) -> list[tuple]:
    """Prepares a list of tag choices suitable for a user's form field.

    This function helps you populate dropdown menus (`<select>`) and similar form
    elements where users need to select from their own tags. Here's how it works:

    1. Fetches the relevant tags for the user, field, and model.
    2. Transforms the tags into a list of tuples, where each tuple has:
        * `value`: The tag name (used by the form)
        * `label`: The tag name (displayed to the user)

    :param model_verbose_name: The display name of the model the field belongs to.
    :param field_name: The display name of the field.
    :param user: The Django User object representing the user whose tags we want.
    :return: A list of tuples, ready to be used for choices in a form field.
    """
    # .. todo:: Need to add handling of this in the widget render method for default
    # Django config,  if none then the value should be ---------
    # Default behaviour is <select> returns first value.
    # choices = [(None, None)].
    choices = []
    user_tags = get_user_field_choices_as_list_or_queryset(
        model_verbose_name=model_verbose_name,
        field_name=field_name,
        user=user,
        return_list=False,
    )  # Get the tags as a QuerySet (efficient)

    for user_tag in user_tags:
        for tag in user_tag.tags.split(","):
            choices.append((tag, tag))  # Build a tuple (value, label)

    return choices


def stdout_with_optional_color(message, color_code=None):
    """
    30	Black
    31	Red
    32	Green
    33	Yellow
    34	Blue
    35	Magenta
    36	Cyan
    37	White
    90	Bright Black (Gray)
    91	Bright Red
    92	Bright Green
    93	Bright Yellow
    94	Bright Blue
    95	Bright Magenta
    96	Bright Cyan
    97	Bright White
    """
    if (
        color_code is not None and sys.stdout.isatty() and os.name != "nt"
    ):  # Check if TTY and not Windows
        message = f"\033[{color_code}m{message}\033[0m"
    sys.stdout.write(message + "\n")


"""
from tag_me.utils import helpers
mvb=UserTag.objects.get(id=1).model_verbose_name
fld=UserTag.objects.get(id=1).field_name
user=UserTag.objects.get(id=1).user
tags=helpers.get_user_field_choices_as_list_tuples(model_verbose_name=mvb, field_name=fld, user=user)
"""
