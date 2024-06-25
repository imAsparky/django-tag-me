"""tag-me app custom forms."""

from django.db.models.fields import forms
from tag_me.db.forms.mixins import TagMeModelFormMixin
from tag_me.models import UserTag
from django.utils.translation import pgettext_lazy as _


class UserTagCreateForm(TagMeModelFormMixin, forms.ModelForm):
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


class UserTagDetailForm(forms.ModelForm):
    """User tag details."""

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


class UserTagUpdateForm(forms.ModelForm):
    """User tag update form"""

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


class UserTagDeleteForm(forms.ModelForm):
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
