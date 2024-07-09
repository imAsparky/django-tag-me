"""blog Views file."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

# from .models import ()


def dashboard(request):
    return render(request, "blog/dashboard.html")


def author(request):
    return render(request, "blog/authors.html")


def all_tags(request):
    return render(request, "blog/all_tags.html")


def user_tags(request):
    return render(request, "blog/user_tags.html")