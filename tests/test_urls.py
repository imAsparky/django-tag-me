"""
Test URL configuration for tag_me tests.

This file provides URL patterns needed for testing views that render templates
referencing external URLs (like allauth's account_logout).
"""

from django.http import HttpResponse
from django.urls import path, include


def dummy_logout_view(request):
    """Dummy logout view for testing."""
    return HttpResponse("Logged out")


def dummy_login_view(request):
    """Dummy login view for testing."""
    return HttpResponse("Login page")


urlpatterns = [
    # Include tag_me URLs
    path("tag-me/", include("tag_me.urls", namespace="tag_me")),
    # Dummy allauth-style account URLs (no namespace - allauth uses flat names)
    path("accounts/logout/", dummy_logout_view, name="account_logout"),
    path("accounts/login/", dummy_login_view, name="account_login"),
]
