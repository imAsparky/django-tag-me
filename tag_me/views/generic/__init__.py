"""Initialise tag-me Generic Views."""

from tag_me.views.generic.base import TagCustomTemplateView
from tag_me.views.generic.detail import TagCustomDetailView
from tag_me.views.generic.detail import TagCustomDetailView
from tag_me.views.generic.edit import (
    TagCustomCreateView,
    TagCustomDeleteView,
    TagCustomFormView,
    TagCustomUpdateView,
)
from tag_me.views.generic.list import TagCustomListView

__all__ = [
    "TagCustomCreateView",
    "TagCustomDeleteView",
    "TagCustomDetailView",
    "TagCustomFormView",
    "TagCustomListView",
    "TagCustomTemplateView",
    "TagCustomUpdateView",
]
