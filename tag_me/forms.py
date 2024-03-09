"""django-tag-me Forms file."""

from django import forms

from tag_me.models import UserTag


class TagCustomModelForm(forms.ModelForm):
    """Custom tag-me model form."""

    def __init__(self, *args, **kwargs):
        # # Add user_id to form
        self.user = kwargs.pop("user", None)
        self.fields["port_tags"].model_verbose_name = kwargs.pop(
            "model_verbose_name", None
        )
        print(f'FORM INIT Verbose {self.fields["port_tags"].__dict__}')
        super().__init__(*args, **kwargs)


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
                self.fields[field].widget.template_name = (
                    "clearable_file_input.html"
                )

                # This will dynamically load the choices in the field
                self.fields[field].widget.choices = [
                    (tag.name, tag.name)
                    for tag in user_tags.filter(field=field)
                ]
