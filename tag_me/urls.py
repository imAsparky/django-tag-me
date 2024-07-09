"""django-tag-me Url's file."""

from django.urls import path

from .views import (
    SynchronisedTagFieldListView,
    TagFieldListView,
    TagManagementView,
    UserTagCreateView,
    UserTagDeleteView,
    UserTagDetailView,
    UserTagListView,
    UserTagUpdateView,
)

# from .views import fnc

app_label = "tag_me"
app_name = "tag_me"

mgmtpatterns = [
    path(
        "mgmt/",
        TagManagementView.as_view(),
        name="tag-mgmt",
    ),
    path(
        "tagged-field-list/",
        TagFieldListView.as_view(),
        name="tagged-field-list",
    ),
    path(
        "sync-tagged-field-list/",
        SynchronisedTagFieldListView.as_view(),
        name="sync-tagged-field-list",
    ),
]

urlpatterns = [
    path(
        "create/tag/",
        UserTagCreateView.as_view(),
        name="create-tag",
    ),
    path(
        "delete/tag/<int:pk>/",
        UserTagDeleteView.as_view(),
        name="delete-tag",
    ),
    path(
        "detail/tag/<int:pk>/",
        UserTagDetailView.as_view(),
        name="detail-tag",
    ),
    path(
        "list/tag/",
        UserTagListView.as_view(),
        name="list-tags",
    ),
    path(
        "update/tag/<int:pk>/",
        UserTagUpdateView.as_view(),
        name="update-tag",
    ),
]

urlpatterns.extend(mgmtpatterns)
