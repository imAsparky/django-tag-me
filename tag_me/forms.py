"""tag-me app custom forms."""

from django.db.models.fields import forms
from django.utils.translation import pgettext_lazy as _

from tag_me.db.forms.mixins import TagMeModelFormMixin
from tag_me.models import UserTag


class UserTagCreateForm(TagMeModelFormMixin, forms.ModelForm):
    """User tag creation form"""

    class Meta:
        model = UserTag
        fields = [
            "tagged_field",
            "user",
            # "content_type",
            "model_verbose_name",
            "field_name",
            "tags",
            # "tag_type",
        ]

        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            # "content_type": _(
            #     "Label",
            #     "Application",
            # ),
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
            # "tag_type": _(
            #     "Label",
            #     "Tag type",
            # ),
        }


class UserTagDetailForm(forms.ModelForm):
    """User tag details."""

    class Meta:
        model = UserTag
        fields = [
            # "tagged_field",
            "user",
            # "content_type",
            "model_verbose_name",
            "field_name",
            "tags",  # This is the tag.
            # "tag_type",
        ]

        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            # "content_type": _(
            #     "Label",
            #     "Application",
            # ),
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
            # "tag_type": _(
            #     "Label",
            #     "Tag type",
            # ),
        }


class UserTagListForm(forms.ModelForm):
    """User tag creation form"""

    class Meta:
        model = UserTag
        fields = [
            "tagged_field",
            "user",
            # "content_type",
            "model_verbose_name",
            "field_name",
            "tags",
            # "tag_type",
        ]

        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            # "content_type": _(
            #     "Label",
            #     "Application",
            # ),
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
            # "tag_type": _(
            #     "Label",
            #     "Tag type",
            # ),
        }


class UserTagUpdateForm(forms.ModelForm):
    """User tag update form"""

    class Meta:
        model = UserTag
        fields = [
            "tagged_field",
            "user",
            # "content_type",
            "model_verbose_name",
            "field_name",
            "tags",
            # "tag_type",
        ]

        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            #             "content_type": _(
            # /044   0003_usertag_tagged_field.py
            #                 "Label",
            #                 "Application",
            #             ),
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
            # "tag_type": _(
            #     "Label",
            #     "Tag type",
            # ),
        }


class UserTagDeleteForm(forms.ModelForm):
    """User tag creation form"""

    class Meta:
        model = UserTag
        fields = [
            "tagged_field",
            "user",
            # "content_type",
            "model_verbose_name",
            "field_name",
            "tags",  # This is the tag.
            # "tag_type",
        ]

        labels = {
            "tagged_field": _(
                "Label",
                "Tagged Field",
            ),
            "user": _(
                "Label",
                "User",
            ),
            # "content_type": _(
            #     "Label",
            #     "Application",
            # ),
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
            # "tag_type": _(
            #     "Label",
            #     "Tag type",
            # ),
        }
