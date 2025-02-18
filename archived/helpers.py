import logging
import os
import sys

from django.contrib.auth.models import AbstractUser

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
                if issubclass(type(field), TagMeCharField):  # Find our tagged fields
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
    """\
    Get Django models that contain TagMeCharField fields.

    Scans through all models in the configured Django apps and returns a list of model
    classes that have at least one TagMeCharField. Uses PROJECT_APPS setting if defined,
    otherwise falls back to INSTALLED_APPS.

    Returns:
       list[models.Model]: List of Django model classes that contain at least one
           TagMeCharField field. Each model appears only once, even if it has multiple
           tagged fields.

    Examples:
       >>> models = get_models_with_tagged_fields()
       >>> [model.__name__ for model in models]
       ['BlogPost', 'Profile']

    Notes:
       - Checks PROJECT_APPS setting first for efficiency, falls back to INSTALLED_APPS
       - Uses ContentType to get models from each app
       - Stops checking fields in a model once first TagMeCharField is found
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
        models = ContentType.objects.filter(app_label=app)  # Get models from the app

        for model in models:
            for field in model.model_class()._meta.fields:
                if issubclass(type(field), TagMeCharField):  # Check for tagged field
                    _tagged_field_models.append(model.model_class())
                    break  # No need to check other fields in this model

    return _tagged_field_models


def get_models_with_tagged_fields_choices() -> list[tuple]:
    """\
    Get list of models with TagMeCharField fields formatted as choices.

    Creates a list of tuples suitable for use in form fields or model choices, containing
    the verbose names of models that have TagMeCharField fields. Includes a null option
    and prevents duplicate entries for models with multiple tagged fields.

    Returns:
       list[tuple]: List of tuples formatted as [(None, None), (verbose_name, verbose_name)].
           The first tuple (None, None) provides a null selection option.
           For all other tuples, both elements contain the model's verbose_name.

    Examples:
       >>> get_models_with_tagged_fields_choices()
       [(None, None), ('blog post', 'blog post'), ('user profile', 'user profile')]

    Notes:
       - Uses get_models_with_tagged_fields() to find relevant models
       - Each model appears only once in the list, even if it has multiple tagged fields
       - Both tuple elements contain the same verbose_name value for consistency
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
    """\
    Get list of TagMeCharField choices for a specific model feature.

    Creates a list of tuples suitable for form fields or model choices, containing
    the verbose names of TagMeCharField fields from a specific model. Includes a null
    option and formats field labels in title case.

    Args:
       feature_name (str, optional): The verbose name of the model to filter by.
           e.g. "blog post". If empty string, returns fields from all models.
           Defaults to "".

    Returns:
       list[tuple]: List of tuples formatted as [(None, None), (label, label)].
           The first tuple (None, None) provides a null selection option.
           For all other tuples, both elements contain the field's verbose_name
           in title case.

    Examples:
       >>> get_model_tagged_fields_choices('blog post')
       [(None, None), ('Title Tags', 'Title Tags'), ('Content Tags', 'Content Tags')]

       >>> get_model_tagged_fields_choices()  # Get all tagged fields
       [(None, None), ('Title Tags', 'Title Tags'), ('Author Tags', 'Author Tags')]

    Notes:
       - Uses get_models_with_tagged_fields() to find models with tagged fields
       - Field labels are automatically title-cased
       - Both tuple elements contain the same label value for consistency
    """
    from tag_me.db.models.fields import TagMeCharField

    if not feature_name:
        feature_name = ""  # Allow filtering by any model

    _tagged_field_list_choices = [(None, None)]  # Placeholder for 'no selection' option

    for model in get_models_with_tagged_fields():
        if model._meta.verbose_name == feature_name:  # Check if we want this model
            for field in model._meta.fields:
                if issubclass(type(field), TagMeCharField):  # Find tagged fields
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
    """\
    Get ContentType for a model based on its verbose name.

    Retrieves the Django ContentType object for a model that has TagMeCharField fields,
    searching by the model's verbose name. If no model is found or no name is provided,
    returns None.

    Args:
       model_verbose_name (str, optional): The verbose name of the model to find.
           e.g. "blog post". Defaults to "".

    Returns:
       ContentType | None: The ContentType object for the requested model if found,
           None if no matching model exists or if no model_verbose_name provided.

    Examples:
       >>> content_type = get_model_content_type('blog post')
       >>> print(content_type.model)
       'blogpost'

       >>> print(get_model_content_type(''))
       None

    Notes:
       - Only searches models that have TagMeCharField fields
       - Uses concrete model types, not proxy models
       - Case-sensitive match on verbose_name
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
    """\
    Get a user's tags for a specific model field as a list or queryset.

    Retrieves tags that a user has created for a specific field in a model, returning
    either a flat list of tag values or the full UserTag queryset.

    Args:
       model_verbose_name (str, optional): The verbose name of the model containing
           the tagged field. e.g. "blog post". Defaults to "".
       field_name (str, optional): Name of the field to get tags for. Defaults to "".
       user (User, optional): User whose tags to retrieve. Defaults to User model class.
       return_list (bool, optional): If True, returns flat list of tag values.
           If False, returns full UserTag queryset. Defaults to True.

    Returns:
       list | models.QuerySet: If return_list is True, returns list of tag values.
           If return_list is False, returns QuerySet of UserTag objects.

    Examples:
       Get list of tag values:
       >>> get_user_field_choices_as_list_or_queryset(
       ...     model_verbose_name='blog post',
       ...     field_name='title_tags',
       ...     user=request.user
       ... )
       ['python', 'django', 'tutorial']

       Get queryset of UserTag objects:
       >>> tags = get_user_field_choices_as_list_or_queryset(
       ...     model_verbose_name='blog post',
       ...     field_name='title_tags',
       ...     user=request.user,
       ...     return_list=False
       ... )
       >>> tags.first().tags
       'python'
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
    user: AbstractUser = User,
) -> list[tuple]:
    """\
    Get a user's tags for a specific model field as list of tuples.

    Retrieves tags that a user has created for a specific field in a model and formats
    them as (value, label) tuples suitable for use in form fields. Each tag from the
    comma-separated tags string becomes a separate choice tuple.

    Args:
       model_verbose_name (str, optional): The verbose name of the model containing
           the tagged field. e.g. "blog post". Defaults to "".
       field_name (str, optional): Name of the field to get tags for. Defaults to "".
       user (User, optional): User whose tags to retrieve. Defaults to User model class.

    Returns:
       list[tuple]: List of tuples where each tuple contains (tag, tag).
           The tag value is used as both the value and label in each tuple.
           Returns empty list if no tags found.

    Examples:
       >>> get_user_field_choices_as_list_tuples(
       ...     model_verbose_name='blog post',
       ...     field_name='title_tags',
       ...     user=request.user
       ... )
       [('python', 'python'), ('django', 'django'), ('tutorial', 'tutorial')]

    Notes:
       - Uses QuerySet for efficient database querying
       - Splits comma-separated tags into individual choices
       - TODO: Add handling in widget render method for default Django config,
         if none then value should be ---------
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
