from typing import Dict, Union
from django.forms import Field
from tag_me.db.forms.fields import TagMeCharField


class TagMeModelFormMixin:
    """
    Mixin for Django ModelForms that enhances TagMeCharField fields.
    """

    fields: Dict[str, Union[TagMeCharField, Field]]

    def __init__(self, *args, user=None, model_verbose_name=None, **kwargs):
        """
        Initializes the form, handling user and model_verbose_name args.
        """
        # Explicitly accept user and model_verbose_name, avoiding kwargs popping
        self.user = user
        self.model_verbose_name = model_verbose_name

        super().__init__(*args, **kwargs)  # Call the original form's __init__

        # Process fields
        for _, field in self.fields.items():
            if isinstance(field, TagMeCharField):
                field.widget.attrs.update({"css_class": "", "user": self.user})
