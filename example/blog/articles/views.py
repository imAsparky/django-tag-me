"""django-tag-me views"""

from django.contrib.auth import logout
from django.shortcuts import redirect

from django.http import request
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import ListView

from tag_me.db.mixins import TagMeArgumentMixin

from .forms import (
    ArticleCreateForm,
    ArticleListForm,
    ArticleUpdateForm,
    AuthorCreateForm,
)


from .models import (
    Article,
    Author,
)


def login(request):
    return render(request, "login.html", {})


def landing(request):
    return render(request, "articles/landing.html", {})


def logout(request):
    logout(request)  # Call Django's logout function
    return redirect("login")


class ArticleCreateView(TagMeArgumentMixin, CreateView):
    """Article creation view"""

    model = Article
    form_class = ArticleCreateForm
    template_name = "articles/article_create.html"
    success_url = reverse_lazy("articles:list-articles")


class ArticleUpdateView(TagMeArgumentMixin, UpdateView):
    """Article creation view"""

    model = Article
    form_class = ArticleUpdateForm
    template_name = "articles/article_update.html"
    success_url = reverse_lazy("articles:list-article")


class ArticleListView(ListView):
    """Article list view."""

    model = Article
    form_class = ArticleListForm
    template_name = "articles/article_list.html"


class AuthorCreateView(CreateView):
    """Author creation view"""

    model = Author
    form_class = AuthorCreateForm
    template_name = "articles/author_create.html"
