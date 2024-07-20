"""django-tag-me Views file."""

from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tag_me.db.mixins import TagMeViewMixin
from tag_me.models import TaggedFieldModel, TagMeSynchronise

from .forms import (  # UserTagDetailForm,; UserTagDeleteForm,; UserTagUpdateForm,
    UserTagCreateForm,
    UserTagDeleteForm,
    UserTagDetailForm,
    UserTagListForm,
    UserTagUpdateForm,
)
from .models import UserTag


class TagManagementView(TemplateView):
    """Tag management dashboard"""

    template_name = "tag_me/mgmt/management.html"


class TagFieldListView(ListView):
    """A list of all the tagged fields."""

    model = TaggedFieldModel
    template_name = "tag_me/mgmt/tagged_field_list.html"


class SynchronisedTagFieldListView(ListView):
    """A list of all the synchronised tagged fields."""

    model = TagMeSynchronise
    template_name = "tag_me/mgmt/sync_tagged_field_list.html"


class UserTagCreateView(TagMeViewMixin, CreateView):
    """Create a new user tag."""

    model = UserTag
    form_class = UserTagCreateForm
    template_name = "tag_me/create_user_tag.html"
    success_url = "/"


class UserTagListView(ListView):
    """List user tags."""

    model = UserTag
    form_class = UserTagListForm
    template_name = "tag_me/list_user_tag.html"
    success_url = "/"


class UserTagDetailView(DetailView):
    """User tag details."""

    model = UserTag
    form_class = UserTagDetailForm
    template_name = "tag_me/detail_user_tag.html"
    success_url = "/"


class UserTagDeleteView(DetailView):
    """User tag details."""

    model = UserTag
    form_class = UserTagDeleteForm
    template_name = "tag_me/detail_user_tag.html"
    success_url = "/"


class UserTagUpdateView(UpdateView):
    """Update user tag."""

    model = UserTag
    form_class = UserTagUpdateForm
    template_name = "tag_me/update_user_tag.html"
    success_url = "/"
