"""Custom django-tag-me list view"""

from django.views.generic import ListView


class TagCustomListView(ListView):
    """
    A custom ListView for the django-tag-me library.

    This view inherits from Django's ListView, adding the current user object
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
