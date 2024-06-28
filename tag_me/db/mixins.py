"""django-tag-me view mixins"""

import logging

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.http import HttpRequest
from django.views.generic.edit import FormMixin

from tag_me.db.forms.mixins import TagMeModelFormMixin

logger = logging.getLogger(__name__)


class TagMeArgumentMixin(FormMixin):
    """
    Mixin for Django CBVs to pass arguments directly to the TagMeModelForm's __init__.
    """

    request: HttpRequest
    # model: Model

    def get_form(self, form_class=None):
        """
        Overrides the get_form method to pass the model_verbose_name directly.
        """
        if form_class is None:
            form_class = self.get_form_class()

        if not issubclass(form_class, TagMeModelFormMixin):
            msg = f"The form {form_class} used with TagMeArgumentMixin must inherit from TagMeModelFormMixin."
            logger.exception(msg)
            raise ImproperlyConfigured(msg)

        form_kwargs = self.get_form_kwargs()

        # Check if user is already in form_kwargs (potentially from another mixin or view)
        if "user" not in form_kwargs:
            form_kwargs["user"] = self.request.user
        form_kwargs["model_verbose_name"] = (self.model._meta.verbose_name,)

        return form_class(
            **self.get_form_kwargs(),
        )
