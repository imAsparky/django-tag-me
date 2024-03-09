"""django-tag-me Forms file."""

from django import forms

from tag_me.models import UserTag


class TagCustomModelForm(forms.ModelForm):
    """
    A custom ModelForm for the django-tag-me library.

    This form class is designed to work with custom Django views (like the
    TagCustom...View classes ) that provide the current user object.
    It enables user-aware logic and filtering within forms.
    """

    model = None  # Placeholder; you would specify your actual model here

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)


class UserTagsBaseForm(TagCustomModelForm):
    """Business creation form."""

    model = None
    tagged_fields: list = [str]  # This should be dynamic

    def __init__(
        self,
        tagged_fields=tagged_fields,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        user_tags = UserTag.objects.all()

        if not tagged_fields:
            ...
        else:
            for field in tagged_fields:
                self.fields[field].widget.template_name = (
                    "clearable_file_input.html"
                )

                # This will dynamically load the choices in the field
                self.fields[field].widget.choices = [
                    (tag.name, tag.name)
                    for tag in user_tags.filter(field=field)
                ]
