"""example tags management"""

from django import urls
from django.urls import include, path
from tags.views import (
    ListAllTaggedFieldView,
    ListAllUserTagsView,
    tags_dashboard,
)

app_label = "tags"
app_name = "tags"

urlpatterns = [
    path(
        "",
        tags_dashboard,
        name="dashboard",
    ),
    path(
        "list-all-tags/",
        ListAllUserTagsView.as_view(),
        name="list-all-tags",
    ),
    path(
        "list-tagged-fields/",
        ListAllTaggedFieldView.as_view(),
        name="list-tagged-fields",
    ),
]
