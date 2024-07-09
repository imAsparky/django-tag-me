"""blog Url's file."""

from django.urls import path

from .views import (
    all_tags,
    author,
    dashboard,
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
