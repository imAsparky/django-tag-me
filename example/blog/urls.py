"""blog Url's file."""

from django.urls import path

from .views import (
    ArticleCreateView,
    all_tags,
    author,
    dashboard,
)

app_name = "blog"
app_label = "blog"


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("author/", author, name="author"),
    path("all-tags/", all_tags, name="all-tags"),
    path(
        "create/article/", ArticleCreateView.as_view(), name="create-article"
    ),
]
