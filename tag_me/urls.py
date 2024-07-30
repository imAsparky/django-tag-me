"""django-tag-me Url's file."""

from django.urls import path

from .views import (
    MgmtUserTagListView,
    SynchronisedTagFieldListView,
    TagFieldListView,
    TaggedFieldEditView,
    TagManagementView,
    UserTagEditView,
    UserTagListView,
    WidgetAddUserTagView,
)

app_label = "tag_me"
app_name = "tag_me"

urlpatterns: list = []

mgmt_urls = [
    path(
        "mgmt/",
        TagManagementView.as_view(),
        name="tag-mgmt",
    ),
    path(
        "list/tag/",
        MgmtUserTagListView.as_view(),
        name="list-tags",
    ),
    path(
        "tagged-field-edit/<int:pk>/",
        TaggedFieldEditView.as_view(),
        name="tagged-field-edit",
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

tag_urls = [
    path(
        "list/tag/<uuid:pk>/",
        UserTagListView.as_view(),
        name="list-user-tags",
    ),
    path(
        "edit/tag/<int:pk>/",
        UserTagEditView.as_view(),
        name="edit-tag",
    ),
    path(
        "add/tag/<int:pk>/",
        WidgetAddUserTagView.as_view(),
        name="add-tag",
    ),
]

urlpatterns.extend(mgmt_urls)
urlpatterns.extend(tag_urls)
