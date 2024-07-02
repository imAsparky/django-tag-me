"""django-tag-me views"""

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from tag_me.db.mixins import TagMeViewMixin

from .forms import ArticleCreateForm, ArticleListForm, AuthorCreateForm
from .models import Article, Author


def index(request):
    return render(request, "index.html", {})


class ArticleCreateView(TagMeViewMixin, CreateView):
    """Article creation view"""

    model = Article
    form_class = ArticleCreateForm
    template_name = "articles/article_create.html"
    success_url = reverse_lazy("articles:list-articles")


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
