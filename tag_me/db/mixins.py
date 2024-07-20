"""django-tag-me view mixins"""

import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.views.generic.edit import FormMixin

from tag_me.db.forms.mixins import TagMeModelFormMixin

logger = logging.getLogger(__name__)


class TagMeViewMixin(FormMixin):
    """
    Mixin for Django CBVs to handle forms with tagged fields.
    Passes the model's verbose name and current user to the TagMeModelForm.
    """

    request: HttpRequest

    def get_form(self, form_class=None):
        """
        Overrides the get_form method to pass the user and model_verbose_name.
        """
        if form_class is None:
            form_class = self.get_form_class()

        if not issubclass(form_class, TagMeModelFormMixin):
            msg = f"The form {form_class} used with TagMeViewMixin must inherit from TagMeModelFormMixin."
            logger.exception(msg)
            raise ImproperlyConfigured(msg)

        form_kwargs = self.get_form_kwargs()

        # Check if user is already in form_kwargs (potentially from another mixin or view)
        if "user" not in form_kwargs:
            form_kwargs["user"] = self.request.user
        form_kwargs["model_verbose_name"] = (self.model._meta.verbose_name,)
        form_kwargs["model_obj"] = self.model
        return form_class(
            **form_kwargs,
        )

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = super().get_initial()
        initial["user"] = self.request.user
        initial["content_type"] = ContentType.objects.get_for_model(
            self.model, for_concrete_model=True
        )
        initial["model_verbose_name"] = self.model.__dict__["_meta"].__dict__[
            "verbose_name"
        ]
        return initial
