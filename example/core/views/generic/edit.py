"""example Core App Generic Views Edit."""

from core.views.generic.base import HtmxTemplateResponseMixin
from django.views.generic import CreateView, DeleteView, FormView, UpdateView


class HtmxCreateView(HtmxTemplateResponseMixin, CreateView):
    """Extends Django List view with HTMX functionality.

    Renders an htmx template or a generic template response.
    """


class HtmxDeleteView(HtmxTemplateResponseMixin, DeleteView):
    """Extends Django Delete view with HTMX functionality.

    Renders an htmx template or a generic template response.
    """


class HtmxFormView(HtmxTemplateResponseMixin, FormView):
    """Extends Django Form view with HTMX functionality.

    Renders an htmx template or a generic template response.
    """


class HtmxUpdateView(HtmxTemplateResponseMixin, UpdateView):
    """Extends Django Update view with HTMX functionality.

    Renders an htmx template or a generic template response.
    """
