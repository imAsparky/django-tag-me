"""django-tag-me Views file."""

import json
import base64
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from tag_me.utils.collections import FieldTagListFormatter
from tag_me.models import (
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)

from .forms import (
    UserTagListForm,
    UserTagEditForm,
)


def try_widget(request):
    return render(request, "tag_me/mgmt/try_tags.html")


class TagManagementView(TemplateView):
    """Tag management dashboard"""

    template_name = "tag_me/mgmt/management.html"


class TagFieldListView(ListView):
    """A list of all the tagged fields."""

    model = TaggedFieldModel
    template_name = "tag_me/mgmt/tagged_field_list.html"


class SynchronisedTagFieldListView(ListView):
    """A list of all the synchronised tagged fields."""

    model = TagMeSynchronise
    template_name = "tag_me/mgmt/sync_tagged_field_list.html"


class UserTagListView(ListView):
    """List user tags."""

    model = UserTag
    form_class = UserTagListForm
    template_name = "tag_me/mgmt/list_user_tag.html"
    success_url = "/"


class UserTagEditView(UpdateView):
    """Update user tag."""

    model = UserTag
    form_class = UserTagEditForm
    template_name = "tag_me/mgmt/edit_user_tag.html"
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usertag"] = UserTag.objects.get(id=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        usertag = UserTag.objects.get(id=self.kwargs["pk"])
        usertag.tags = form.cleaned_data["tags"]
        usertag.save()
        return super().form_valid(form)


class WidgetAddUserTagView(View):
    def post(self, request, *args, **kwargs):
        encoded_data = None
        user_tag = None
        encoded_data = request.POST.get("encoded_tag")

        if not encoded_data:
            return JsonResponse({"error": "Invalid or corrupted tag data"}, status=400)

        try:
            data = json.loads(base64.urlsafe_b64decode(encoded_data).decode("utf-8"))
            user_tag = UserTag.objects.get(id=self.kwargs["pk"])
            all_tags = FieldTagListFormatter(user_tag.tags)
            all_tags.add_tags(data)
            user_tag.tags = all_tags.toCSV()
            user_tag.save()

            return JsonResponse(
                {
                    "success": True,
                    "tags": all_tags.toList(),
                }
            )
        except (json.JSONDecodeError, base64.binascii.Error, user_tag.DoesNotExist):
            return JsonResponse({"error": "Invalid or corrupted data"}, status=400)
