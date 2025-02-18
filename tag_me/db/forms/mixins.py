import logging
from typing import Union

from django import forms
from django.core.exceptions import ObjectDoesNotExist

from tag_me.db.forms.fields import TagMeCharField
from tag_me.models import TaggedFieldModel, UserTag
from tag_me.widgets import TagMeSelectMultipleWidget

logger = logging.getLogger(__name__)


class TagMeModelFormMixin:
    """
    Mixin for Django ModelForms that enhances TagMeCharField fields.

    This mixin provides additional configuration and behavior for `TagMeCharField` fields within a ModelForm. It allows for customization based on the current user.
    """

    fields: dict[str, Union[TagMeCharField, forms.Field]]

    def __init__(self, *args, **kwargs):
        """
        Initializes the form, extracting the current user from keyword arguments.

        Args:
            *args: Variable length argument list passed to the parent ModelForm's __init__.
            **kwargs: Arbitrary keyword arguments passed to the parent ModelForm's __init__.
                 - user: (Optional) The current user object.
        """

        self.user = kwargs.pop("user", None)
        self.model_obj = kwargs.pop("model_obj", None)
        self.model_verbose_name = kwargs.pop("model_verbose_name", None)
        self.model_name = kwargs.pop("model_name", None)
        super().__init__(*args, **kwargs)  # Call the original form's __init__

        # Process fields
        for _, field in self.fields.items():
            if isinstance(field, TagMeCharField):
                field.widget.attrs.update(
                    {
                        "css_class": "",
                        "user": self.user,
                    }
                )


class AllFieldsTagMeModelFormMixin:
    """
    Mixin for Django ModelForms that enhances TagMeCharField fields.

    This mixin provides additional configuration and behavior for `TagMeCharField` fields within a ModelForm. It allows for customization based on the current user.
    """

    fields: dict[str, Union[TagMeCharField, forms.Field]]

    def __init__(self, *args, **kwargs):
        """
        Initializes the form, extracting the current user from keyword arguments.

        Args:
            *args: Variable length argument list passed to the parent ModelForm's __init__.
            **kwargs: Arbitrary keyword arguments passed to the parent ModelForm's __init__.
                 - user: (Optional) The current user object.
        """

        self.user = kwargs.pop("user", None)
        if self.user is None:
            msg = "User is required for AllFieldsTagMeModelFormMixin"
            logger.exception(msg)
            raise ObjectDoesNotExist(msg)
        super().__init__(*args, **kwargs)

        tagged_models = TaggedFieldModel.objects.all()
        user_tags = UserTag.objects.filter(user=self.user)
        # Get the user tag to process
        for tagged_model in tagged_models:
            try:
                user_tag = user_tags.get(
                    model_name=tagged_model.model_name,
                    field_name=tagged_model.field_name,
                )
                self.fields[user_tag.field_name] = forms.CharField(
                    required=False,
                    label=user_tag.field_verbose_name,
                    widget=TagMeSelectMultipleWidget(
                        attrs={
                            "all_tag_fields_mixin": True,
                            "display_all_tags": False,
                            "user": self.user,
                            "all_tag_fields_tag_string": user_tag.tags,
                        },
                    ),
                )
            except ObjectDoesNotExist:
                msg = f"User Tag does not exist {tagged_model.model_name}:{tagged_model.field_name}"
                logger.exception(msg)
