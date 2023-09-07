"""django-tag-me Forms file."""

from django import forms

from tag_me.models import UserTag


class UserTagsBaseForm(forms.ModelForm):
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
                self.fields[
                    field
                ].widget.template_name = "clearable_file_input.html"

                # This will dynamically load the choices in the field
                self.fields[field].widget.choices = [
                    (tag.name, tag.name)
                    for tag in user_tags.filter(field=field)
                ]
