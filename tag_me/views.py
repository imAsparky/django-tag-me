"""django-tag-me Views file."""

from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tag_me.db.mixins import TagMeViewMixin

from .forms import (  # UserTagDetailForm,; UserTagDeleteForm,; UserTagUpdateForm,
    UserTagCreateForm,
    UserTagListForm,
)
from .models import UserTag


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


# class UserTagDetailView(DetailView):
#     """User tag details."""
#
#     model = UserTag
#     form_class = UserTagDetailForm
#     template_name = "tag_me/detail_user_tag.html"
#     success_url = "/"
#
#
# class UserTagDeleteView(DetailView):
#     """User tag details."""
#
#     model = UserTag
#     form_class = UserTagDeleteForm
#     template_name = "tag_me/detail_user_tag.html"
#     success_url = "/"
#
#
# class UserTagUpdateView(UpdateView):
#     """Update user tag."""
#
#     model = UserTag
#     form_class = UserTagUpdateForm
#     template_name = "tag_me/update_user_tag.html"
#     success_url = "/"
