"""Custom django-tag-me edit views"""

from typing import override
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    UpdateView,
)


class TagMeCreateView(CreateView):
    """
    A custom CreateView for the django-tag-me library.

    This view inherits from Django's CreateView, adding the current user object
    to the template context. This enables potential user-specific filtering or
    customization when rendering lists of objects in templates.
    """

    @override
    def get_form_kwargs(self):
        """
        Overrides the parent class's get_form_kwargs method to inject the user object. # noqa: E501

        This method is responsible for preparing keyword arguments that are
        passed to a form during initialization. By adding the 'user'  object,
        it enables forms to implement user-based filtering or customization.

        :return: A dictionary of keyword arguments, including the 'user' and 'model_verbose_name' objects. # noqa: E501
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["model_verbose_name"] = self.model._meta.verbose_name
        return kwargs


class TagMeDeleteView(DeleteView):
    """
    A custom DeleteView for the django-tag-me library.

    This custom view inherits from Django's DeleteView and provides a
    consistent way to potentially pass the current user object to forms, even
    though forms might not be strictly required in the default deletion
    process. This facilitates future customization and integration with
    django-tag-me.
    """

    @override
    def get_form_kwargs(self):
        """
        Overrides the parent class's get_form_kwargs method to potentially inject the user object. # noqa: E501

        While forms might not be directly used in a default DeleteView,  this
        override ensures the 'user'  object is available if you add custom
        logic or forms in the future.

        :return: A dictionary of keyword arguments, including the 'user' and 'model_verbose_name' objects. # noqa: E501
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["model_verbose_name"] = self.model._meta.verbose_name
        return kwargs


class TagMeFormView(FormView):
    """
    A custom FormView for the django-tag-me library.

    This view inherits from Django's FormView, adding the current user object
    to the template context. This enables potential user-specific filtering or
    customization when rendering lists of objects in templates.
    """

    @override
    def get_form_kwargs(self):
        """
        Overrides the parent class's get_form_kwargs method to inject the user object. # noqa: E501

        This method is responsible for preparing keyword arguments that are
        passed to a form during initialization. By adding the 'user'  object,
        it enables forms to implement user-based filtering or customization.

        :return: A dictionary of keyword arguments, including the 'user' and 'model_verbose_name' objects. # noqa: E501
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["model_verbose_name"] = self.model._meta.verbose_name
        return kwargs


class TagMeUpdateView(UpdateView):
    """
    A custom UpdateView for the django-tag-me library.

    This custom view extends Django's built-in UpdateView, adding the current
    user object to the form's keyword arguments.  This ensures that
    user-specific data filtering can be applied within forms used for updating.
    """

    @override
    def get_form_kwargs(self):
        """
        Overrides the parent class's get_form_kwargs method to inject the user object. # noqa: E501

        This method is responsible for preparing keyword arguments that are
        passed to a form during initialization. By adding the 'user'  object,
        it enables forms to implement user-based filtering or customization.

        :return: A dictionary of keyword arguments, including the 'user' and 'model_verbose_name' objects. # noqa: E501
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["model_verbose_name"] = self.model._meta.verbose_name
        return kwargs
