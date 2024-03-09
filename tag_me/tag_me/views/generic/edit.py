"""Custom django-tag-me edit views"""

from typing import override
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    UpdateView,
)


class TagCustomCreateView(CreateView):
    """
    A custom CreateView for the django-tag-me library.

    This view inherits from Django's CreateView, adding the current user object
    to the template context. This enables potential user-specific filtering or
    customization when rendering lists of objects in templates.
    """

    def get_context_data(self, **kwargs):
        """
        Overrides the parent class's get_context_data method to include the user object. # noqa: E501

        This method is responsible for compiling the data that will be
        available to the template. By adding the 'user' object, it can be used
        in the template as needed.

        :return: A dictionary of context data, including the 'user' object.
        """

        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class TagCustomDeleteView(DeleteView):
    """
    A custom DeleteView for the django-tag-me library.

    This custom view inherits from Django's DeleteView and provides a
    consistent way to potentially pass the current user object to forms, even
    though forms might not be strictly required in the default deletion
    process. This facilitates future customization and integration with
    django-tag-me.
    """

    def get_form_kwargs(self):
        """
        Overrides the parent class's get_form_kwargs method to potentially inject the user object. # noqa: E501

        While forms might not be directly used in a default DeleteView,  this
        override ensures the 'user'  object is available if you add custom
        logic or forms in the future.

        :return: A dictionary of keyword arguments, potentially including the 'user' object. # noqa: E501
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TagCustomFormView(FormView):
    """
    A custom FormView for the django-tag-me library.

    This view inherits from Django's FormView, adding the current user object
    to the template context. This enables potential user-specific filtering or
    customization when rendering lists of objects in templates.
    """

    def get_context_data(self, **kwargs):
        """
        Overrides the parent class's get_context_data method to include the user object. # noqa: E501

        This method is responsible for compiling the data that will be
        available to the template. By adding the 'user' object, it can be used
        in the template as needed.

        :return: A dictionary of context data, including the 'user' object.
        """

        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class TagCustomUpdateView(UpdateView):
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

        :return: A dictionary of keyword arguments, including the 'user' object. # noqa: E501
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
