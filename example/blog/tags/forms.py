"""example tags forms."""

from django.db.models.fields import forms
from django.utils.translation import pgettext_lazy as _

from tag_me.db.forms.mixins import TagMeModelFormMixin
from tag_me.models import TaggedFieldModel, UserTag


class UserTagListForm(forms.ModelForm):
    """User tag creation form"""

    class Meta:
        model = UserTag
        fields = [
            "user",
            "content_type",
            "model_verbose_name",
            "field_name",
            "name",  # This is the tag.
        ]

        labels = {
            "user": _(
                "Label",
                "User",
            ),
            "content_type": _(
                "Label",
                "Application",
            ),
            "model_verbose_name": _(
                "Label",
                "Feature",
            ),
            "field_name": _(
                "Label",
                "Field",
            ),
            "name": _(
                "Label",
                "Tag name",
            ),
        }


class TaggedFieldsListForm(forms.ModelForm):
    """Tagged model fields list"""

    class Meta:
        model = TaggedFieldModel
        fields = [
            "content",
            "model_name",
            "model_verbose_name",
            "field_name",
            "field_verbose_name",
        ]
        labels = {
            "content": _(
                "Label",
                "App/Content name",
            ),
            "model_verbose_name": _(
                "Label",
                "Model Verbose/Feature name",
            ),
            "model_name": _(
                "Label",
                "Model name",
            ),
            "field_name": _(
                "Label",
                "Field name",
            ),
            "field_verbose_name": _(
                "Label",
                "Field verbose name",
            ),
        }
