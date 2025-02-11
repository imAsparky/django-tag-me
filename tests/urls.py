"""tests Url's file."""

from django.urls import include, path

# from .views import ()
app_label = "tests"
app_name = "tests"

urlpatterns = [
    path("", include("tag_me.urls", namespace="tag_me")),
]
