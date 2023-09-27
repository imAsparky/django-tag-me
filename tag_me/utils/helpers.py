import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models

from tag_me.db.models.fields import TagMeCharField

# from tags.db.models import TaggedFieldJSONField
from tag_me.models import TaggedFieldModel, UserTag

User = get_user_model()
logger = logging.getLogger(__name__)


def update_models_with_tagged_fields_table() -> None:
    """Update the Tagged Field Models table.

    Iterates through the Tagged Field Models and updates or creates the model
    and field attributes in the `TaggedFieldModel` table.
    """
    for model in get_models_with_tagged_fields():
        content = ContentType.objects.get_for_model(
            model, for_concrete_model=True
        )

        model_name = content.model_class().__name__
        model_verbose_name = content.model_class()._meta.verbose_name

        for field in get_model_tagged_fields_field_and_verbose(
            model_verbose_name=model_verbose_name,
        ):
            match field[0]:
                case None:
                    # We test for None because the first tuple returned is None
                    pass
                case _:
                    (
                        obj,
                        created,
                    ) = TaggedFieldModel.objects.update_or_create(
                        content=content,
                        field_name=field[0],
                        field_verbose_name=field[1],
                        model_name=model_name,
                        model_verbose_name=model_verbose_name,
                    )

                    match created:
                        case True:
                            logger.info(f"\tCreated {obj} : {field[0]}")
                        case False:
                            logger.info(f"\tUpdated {obj} : {field[0]}")


def get_model_tagged_fields_field_and_verbose(
    model_verbose_name: str = None,
) -> list[tuple]:
    """Return a list of tuples containing a models tagged fields name and verbose name. # noqa: E501

    Use this for <select> options in Forms, eg `form.ModelChoices`.

    :return: Returns a list of tuples with `field_name` and `field_verbose_name`. # noqa: E501

    :rtype: list[tuple()]

    """

    if not model_verbose_name:
        model_verbose_name = ""

    _tagged_field_list_choices = [(None, None)]

    for model in get_models_with_tagged_fields():
        if model._meta.verbose_name == model_verbose_name:
            for field in model._meta.fields:
                # if type(field) is TaggedFieldJSONField:
                if issubclass(type(field), TagMeCharField):
                    label = str(
                        model._meta.get_field(field.name).verbose_name.title()
                    )
                    value = field.name
                    _tagged_field_list_choices.append(
                        (value, label),
                    )

    return _tagged_field_list_choices


def get_models_with_tagged_fields() -> list[models.Model]:
    """Return a list of models that have tagged fields.

    Gets all the models from Content Types and tests the fields for
    :class: TaggedFieldField class, and if it exists the model is added to
    the list.

    :return: A list of models that have tagged fields.

    :rtype: list
    """
    # Separating project apps into PROJECT_APPS makes it more efficient.
    # If user has all apps in INSTALLED_APPS then use that.
    match settings.PROJECT_APPS:
        case None:
            PROJECT_APPS = settings.INSTALLED_APPS
        case _:
            PROJECT_APPS = settings.PROJECT_APPS

    _tagged_field_models = []
    for app in PROJECT_APPS:
        # Left for reference, can be deleted any time.
        # we dont want the testing models in the users options
        # if (
        #     app != "testing_core"
        #     and settings.SETTINGS_MODULE != "config.settings.test"
        # ):
        #     app = app

        # # we want the testing models in the test environment for users options # noqa: E501
        # elif settings.SETTINGS_MODULE == "config.settings.test":
        #     app = app

        # else:
        #     break

        models = ContentType.objects.filter(app_label=app)
        for model in models:
            for field in model.model_class()._meta.fields:
                # if type(field) is TaggedFieldJSONField:
                if issubclass(type(field), TagMeCharField):
                    _tagged_field_models.append(model.model_class())
                    # return back to the model loop, prevents duplicates in list. # noqa: E501
                    break

    return _tagged_field_models


def get_models_with_tagged_fields_choices() -> list[tuple]:
    """
    Return a list of tuples with humanised value for models that have tagged fields.  # noqa: E501

    Use this for <select> options in Forms, eg `form.ModelChoices`.

    These tuples provide a nice human readable `value` for display in tables
    accessed by the user.

    :return: Returns a list of tuples with `object_name` and
            `model_verbose_name`.

    :rtype: list[tuple()]
    """

    _tagged_field_model_choices = [(None, None)]
    for model in get_models_with_tagged_fields():
        for field in model._meta.fields:
            # if type(field) is TaggedFieldJSONField:
            if issubclass(type(field), TagMeCharField):
                label = model._meta.verbose_name
                value = label
                # value = model._meta.object_name
                _tagged_field_model_choices.append(
                    (value, label),
                )
                # return back to the model loop, prevents duplicates in list.
                break

    return _tagged_field_model_choices


def get_model_tagged_fields_choices(
    feature_name: str = None,
) -> list[tuple]:
    """Return a list of tuples containing a models tagged fields name and verbose name. # noqa: E501

    Use this for <select> options in Forms, eg `form.ModelChoices`.

    :return: Returns a list of tuples with `field_name` and `field_verbose_name`.

    :rtype: list[tuple()]

    """

    if not feature_name:
        feature_name = ""

    _tagged_field_list_choices = [(None, None)]

    for model in get_models_with_tagged_fields():
        if model._meta.verbose_name == feature_name:
            for field in model._meta.fields:
                # if type(field) is TaggedFieldJSONField:
                if issubclass(type(field), TagMeCharField):
                    label = str(
                        model._meta.get_field(field.name).verbose_name.title()
                    )
                    value = label
                    _tagged_field_list_choices.append(
                        (value, label),
                    )

    return _tagged_field_list_choices


def get_model_content_type(
    model_verbose_name: str = None,
) -> ContentType:
    """Return a :class: ContentType for the model.


    :return: Returns a ContentType for a models verbose_name`.

    :rtype: ContentType

    """

    if not model_verbose_name:
        return None

    for model in get_models_with_tagged_fields():
        if model._meta.verbose_name == model_verbose_name:
            content_type = ContentType.objects.get_for_model(
                model=model,
                for_concrete_model=True,
            )
            return content_type


def get_field_choices(
    model_verbose_name: str = None,
    field_verbose_name: str = None,
    user: User = None,
) -> list[tuple]:
    """Get the available choices for a model field.

    .. todo:: Add a check for existing field choice enum and return it.
    """

    choices = UserTag.objects.filter(
        feature=model_verbose_name,
        field=field_verbose_name,
        user=user,
    )

    return choices
