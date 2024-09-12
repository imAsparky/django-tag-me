"""tag-me app custom forms."""

from django.db.models.fields import forms
from django.utils.translation import pgettext_lazy as _

from tag_me.db.forms.mixins import TagMeModelFormMixin
from tag_me.models import (
    UserTag,
    TaggedFieldModel,
)


class TaggedFieldEditForm(TagMeModelFormMixin, forms.ModelForm):
    class Meta:
        model = TaggedFieldModel
        fields = "__all__"

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        # Iterate over model fields, add non-editable fields to form.
        for field in self.Meta.model._meta.get_fields():
            if (
                not field.editable and field.name not in self.fields
            ):  # Check if already in self.fields
                # Create a BoundField for the non-editable field
                self.fields[field.name] = forms.CharField(
                    initial=getattr(self.instance, field.name),  # Set initial value
                    widget=forms.TextInput(attrs={"readonly": True}),
                    required=False,  # Non-editable fields shouldn't be required
                )


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
            "ui_display_name": _(
                "Label",
                "UI Display Name`",
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
            "field_verbose_name": _(
                "Label",
                "Tagged Field",
            ),
            "ui_display_name": _(
                "Label",
                "UI Display Name",
            ),
            "tags": _(
                "Label",
                "Tags",
            ),
            "comment": _(
                "Label",
                "Comment",
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        # Iterate over model field, add non-editable fields to the form.
        for field in self.Meta.model._meta.get_fields():
            if (
                not field.editable and field.name not in self.fields
            ):  # Check if already in self.fields
                # Create a BoundField for the non-editable field
                label = self.Meta.labels.get(field.name, field.verbose_name)
                self.fields[field.name] = forms.CharField(
                    label=label,
                    initial=getattr(self.instance, field.name),  # Set initial value
                    widget=forms.TextInput(attrs={"readonly": True}),
                    required=False,  # Non-editable fields shouldn't be required
                )


class UserTagDeleteForm(forms.ModelForm):
    """User tag creation form.
    Probably needs to be deleted when the edit forms are completed.
    """

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
            "ui_display_name": _(
                "Label",
                "UI Display Name`",
            ),
            "tags": _(
                "Label",
                "Tag name",
            ),
        }
