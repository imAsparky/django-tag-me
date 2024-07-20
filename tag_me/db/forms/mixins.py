from typing import Dict, Union

from django.forms import Field

from tag_me.db.forms.fields import TagMeCharField
from tag_me.models import TaggedFieldModel, UserTag


class TagMeModelFormMixin:
    """
    Mixin for Django ModelForms that enhances TagMeCharField fields.

    This mixin provides additional configuration and behavior for `TagMeCharField` fields within a ModelForm. It allows for customization based on the current user.
    """

    fields: Dict[str, Union[TagMeCharField, Field]]

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
            # self.fields["field"].initial = obj._meta.get_field(field_name).verbose_name
            if isinstance(field, TagMeCharField):
                field.widget.attrs.update(
                    {
                        "css_class": "",
                        "user": self.user,
                    }
                )
                # self.fields["field"].initial = field
