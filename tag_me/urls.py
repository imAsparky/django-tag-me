"""django-tag-me Url's file."""

from django.urls import include, path

from .views import UserTagCreateView, UserTagListView
# from .views import fnc

app_label = "tag_me"
app_name = "tag_me"

urlpatterns = [
    path(
        "create/tag/",
        UserTagCreateView.as_view(),
        name="create-tag",
    ),
    path(
        "list/tag/",
        UserTagListView.as_view(),
        name="list-tags",
    ),
]
