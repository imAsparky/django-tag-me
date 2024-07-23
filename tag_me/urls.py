"""django-tag-me Url's file."""

from django.urls import path

from .views import (
    SynchronisedTagFieldListView,
    TagFieldListView,
    TagManagementView,
    # UserTagCreateView,
    # UserTagDeleteView,
    # UserTagDetailView,
    UserTagListView,
    UserTagEditView,
    WidgetAddUserTagView,
    try_widget,
)

# from .views import fnc

app_label = "tag_me"
app_name = "tag_me"

urlpatterns: list = []

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

tagpatterns = [
    path(
        "list/tag/",
        UserTagListView.as_view(),
        name="list-tags",
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
    path(
        "try/",
        try_widget,
        name="try-widget",
    ),
]

urlpatterns.extend(mgmtpatterns)
urlpatterns.extend(tagpatterns)
