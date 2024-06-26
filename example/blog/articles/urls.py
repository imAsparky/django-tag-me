"""django-tag-me urls"""

from django.urls import path
from .views import (
    login,
    logout,
    landing,
    ArticleCreateView,
    ArticleListView,
    ArticleUpdateView,
    AuthorCreateView,
)

app_label = "articles"
app_name = "articles"

urlpatterns = [
    path(
        "",
        login,
        name="login",
    ),
    path(
        "logout/",
        logout,
        name="logout",
    ),
    path(
        "landing/",
        landing,
        name="landing",
    ),
    path(
        "create/article/",
        ArticleCreateView.as_view(),
        name="create-article",
    ),
    path(
        "list/article/",
        ArticleListView.as_view(),
        name="list-articles",
    ),
    path(
        "update/article/<int:pk>/",
        ArticleUpdateView.as_view(),
        name="update-article",
    ),
    path(
        "create/author/",
        AuthorCreateView.as_view(),
        name="create-author",
    ),
]
