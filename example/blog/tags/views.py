"""example tags views file"""

from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tag_me.db.mixins import TagMeArgumentMixin
from tag_me.models import TaggedFieldModel, UserTag

from .forms import (  # UserTagCreateForm,; UserTagDetailForm,; UserTagDeleteForm,; UserTagUpdateForm,
    TaggedFieldsListForm,
    UserTagListForm,
)


def tags_dashboard(request):
    """Tag management dashboard"""
    return render(request, "tags/tags_dashboard.html")


class ListAllUserTagsView(ListView):
    """List user tags."""

    model = UserTag
    form_class = UserTagListForm
    template_name = "tags/list_all_tags.html"


class ListAllTaggedFieldView(ListView):
    """List user tags."""

    model = TaggedFieldModel
    form_class = TaggedFieldsListForm
    template_name = "tags/list_all_tagged_fields.html"
