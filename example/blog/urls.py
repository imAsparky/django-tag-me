"""blog Url's file."""

from django.urls import path

from .views import (
    ArticleTagsCreateView,
    ArticleTagsUpdateForm,
    ArticleTagsUpdateView,
    all_tags,
    author,
    dashboard,
    user_tags,
)

app_name = "blog"
app_label = "blog"


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("author/", author, name="author"),
    path("all-tags/", all_tags, name="all-tags"),
    path("user-tags/", user_tags, name="user-tags"),
    path(
        "add-user-tags/", ArticleTagsCreateView.as_view(), name="add-user-tags"
    ),
    path(
        "update-user-tags/<int:pk>/",
        ArticleTagsUpdateView.as_view(),
        name="update-user-tags",
    ),
]
