"""tag-me app custom forms."""

from django.db.models.fields import forms
from django.db.models.query_utils import select_related_descend
from django.utils.translation import pgettext_lazy as _

# from tag_me import widgets
from tag_me.db.forms.fields import TagMeCharField
from tag_me.models import (
    UserTag,
    TaggedFieldModel,
)


class TaggedFieldEditForm(forms.ModelForm):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        for field in self.Meta.model._meta.get_fields():
            if not field.editable:
                self.fields[field.name].widget.attrs.update(
                    {
                        "readonly": True,
                        "disabled": True,
                    }
                )

    class Meta:
        model = TaggedFieldModel
        fields = "__all__"


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
            "field_verbose_name": _(
                "Label",
                "Tagged Field",
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
        # Iterate over model fields
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
