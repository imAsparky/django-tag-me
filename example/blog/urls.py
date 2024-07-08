"""blog Url's file."""

from django.urls import include, path

from .views import (
    dashboard,
    author,
    all_tags,
    user_tags,
)

app_name = "blog"
app_label = "blog"


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("author", author, name="author"),
    path("all-tags", all_tags, name="all-tags"),
    path("user-tags", user_tags, name="user-tags"),
]
