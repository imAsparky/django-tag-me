"""example Core App Generic Views List."""

from core.views.generic.base import HtmxTemplateResponseMixin
from django.views.generic import ListView


class HtmxListView(HtmxTemplateResponseMixin, ListView):
    """Extends Django List view with HTMX functionality.

    Renders an htmx template or a generic template response.
    """
