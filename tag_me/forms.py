"""tag-me app custom forms."""

from django import forms
from tag_me.db.forms.fields import TagMeCharField
from tag_me.models import UserTag


class TagMeModelForm(forms.ModelForm):
    """Custom ModelForm designed for use with TagMeCharField fields.

    This form automatically injects user information and styles into any
    TagMeCharField widgets it contains, providing a streamlined experience.

    **Key Features:**

    * **User Awareness:**  Passes the current user to TagMeCharField widgets,
      enabling user-specific customization (likely for tag choices).
    * **Styling:** Adds CSS classes to TagMeCharField widgets for consistent
      visual appearance.

    **Usage:**

    1. Define a Django model that includes one or more TagMeCharField fields.
    2. Use `TagMeModelForm` as the base class for a form tied to this model.

    """

    def __init__(self, *args, **kwargs):
        """Initializes the form, extracting the user for later use.

        Args:
            :param user (User):  The Django User object representing the
                                 currently logged-in user. This is supplied
                                 via the 'get_form_kwargs' method in a
                                 Django view
            :param *args:  Additional positional arguments to pass to the parent
                           ModelForm's constructor.
            :param **kwargs:  Additional keyword arguments to pass to the parent
                              ModelForm's constructor.
        """
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if isinstance(
                field, TagMeCharField
            ):  # Check if it's a TagMeCharField field
                self.fields[field_name].widget.attrs.update(
                    {
                        "css_class": "",
                        "user": self.user,
                    }
                )


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
