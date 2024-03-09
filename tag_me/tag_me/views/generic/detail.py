"""Custom django-tag-me detail view"""

from django.views.generic import DetailView


class TagCustomDetailView(DetailView):
    """
    A custom DetailView for the django-tag-me library.

    This view extends Django's DetailView, adding the current user object to
    the template context. This allows templates to potentially utilize
    user-specific information or filtering when displaying detailed
    information.
    """

    def get_context_data(self, **kwargs):
        """
        Overrides the parent class's get_context_data method to include the user object. # noqa:E501

        This method prepares the data that will be rendered in the template.
        By adding the 'user' object, template code can access and use it as
        needed.

        :return: A dictionary of context data, including the 'user' object.
        """

        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context
