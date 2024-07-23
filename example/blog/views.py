"""blog Views file."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tag_me.db.mixins import TagMeViewMixin
from .forms import (
    ArticleCreateForm,
    ArticleUpdateForm,
)
from .models import Article, Author


class ArticleCreateView(TagMeViewMixin, CreateView):
    """Article tags creation"""

    model = Article
    form_class = ArticleCreateForm
    template_name = "blog/create_article.html"
    success_url = reverse_lazy("blog:user-tags")


def dashboard(request):
    return render(request, "blog/dashboard.html")


def author(request):
    return render(request, "blog/authors.html")


def all_tags(request):
    return render(request, "blog/all_tags.html")


def user_tags(request):
    return render(request, "blog/user_tags.html")
