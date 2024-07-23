"""tag-me app custom forms."""

from django.db.models.fields import forms
from django.utils.translation import pgettext_lazy as _

from tag_me.models import UserTag


class UserTagListForm(forms.ModelForm):
    """User tag creation form"""

    class Meta:
        model = UserTag
        fields = "__all__"
        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            "model_verbose_name": _(
                "Label",
                "Feature",
            ),
            "field_name": _(
                "Label",
                "Field",
            ),
            "tags": _(
                "Label",
                "Tag name",
            ),
        }


class UserTagEditForm(forms.ModelForm):
    """User tag update form"""

    class Meta:
        model = UserTag
        fields = "__all__"
        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            "model_verbose_name": _(
                "Label",
                "Feature",
            ),
            "field_name": _(
                "Label",
                "Field",
            ),
            "tags": _(
                "Label",
                "Tag name",
            ),
            "comment": _(
                "Label",
                "Comment",
            ),
        }


class UserTagDeleteForm(forms.ModelForm):
    """User tag creation form"""

    class Meta:
        model = UserTag
        fields = "__all__"
        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            "model_verbose_name": _(
                "Label",
                "Feature",
            ),
            "field_name": _(
                "Label",
                "Field",
            ),
            "tags": _(
                "Label",
                "Tag name",
            ),
        }
