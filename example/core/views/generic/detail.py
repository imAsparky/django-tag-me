"""example Core App Generic Views Detail."""

from core.views.generic.base import HtmxTemplateResponseMixin
from django.views.generic import DetailView


class HtmxDetailView(HtmxTemplateResponseMixin, DetailView):
    """Extends Django Detail view with HTMX functionality.

    Renders an htmx template or a generic template response.
    """
