"""django-tag-me urls"""

from django.urls import path

from .views import ArticleCreateView, ArticleListView, AuthorCreateView, index

app_label = "articles"
app_name = "articles"

urlpatterns = [
    path(
        "",
        index,
        name="index",
    ),
    path(
        "create/article",
        ArticleCreateView.as_view(),
        name="create-article",
    ),
    path(
        "list/article",
        ArticleListView.as_view(),
        name="list-articles",
    ),
    path(
        "create/author",
        AuthorCreateView.as_view(),
        name="create-author",
    ),
]
