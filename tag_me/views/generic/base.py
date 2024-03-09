from django.views.generic.base import TemplateView


class TagCustomTemplateView(TemplateView):
    """Extends Django Template View with HTMX functionality.

    Renders an htmx template or a generic template response.
    """

    def get_form_kwargs(self):
        """This method adds form keyword arguments.

        Adding kwargs here makes them available in the forms.  The view passes
        the kwargs to forms where they can be popped out in __init__
        """

        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["model_verbose_name"] = self.model._meta.verbose_name

        return kwargs
