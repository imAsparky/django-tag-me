"""django-tag-me Views file."""

import base64
import binascii
import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from tag_me.forms import (
    TaggedFieldEditForm,
    UserTagEditForm,
    UserTagListForm,
)
from tag_me.models import (
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.utils.collections import FieldTagListFormatter

logger = logging.getLogger(__name__)


class TagManagementView(TemplateView):
    """Tag management dashboard"""

    template_name = "tag_me/mgmt/management.html"


class TaggedFieldEditView(UpdateView):
    """Edit the default tags available for users."""

    model = TaggedFieldModel
    form_class = TaggedFieldEditForm
    template_name = "tag_me/mgmt/edit_tagged_fields.html"
    success_url = reverse_lazy("tag_me:tag-mgmt")

    def form_valid(self, form):
        default_tags = FieldTagListFormatter(form.cleaned_data["default_tags"])
        form.cleaned_data["default_tags"] = default_tags.toCSV()

        return super().form_valid(form)


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
    template_name = "tag_me/user/list_user_tag.html"
    success_url = reverse_lazy("tag_me:tag-mgmt")

    def get_context_data(self, *, object_list=None, **kwargs):
        object_list = UserTag.objects.filter(user=self.kwargs["pk"])
        return super().get_context_data(object_list=object_list, **kwargs)


class MgmtUserTagListView(ListView):
    """List user tags."""

    model = UserTag
    form_class = UserTagListForm
    template_name = "tag_me/mgmt/list_user_tag.html"
    success_url = reverse_lazy("tag_me:tag-mgmt")


class UserTagEditView(UpdateView):
    """Update user tag."""

    model = UserTag
    form_class = UserTagEditForm
    template_name = "tag_me/user/edit_user_tag.html"
    success_url = reverse_lazy("tag_me:tag-mgmt")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usertag"] = UserTag.objects.get(id=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        usertag = UserTag.objects.get(id=self.kwargs["pk"])
        usertag.tags = form.cleaned_data["tags"]
        usertag.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class WidgetAddUserTagView(View):
    """Add tags from the TagMeCharfield widget."""

    def post(self, request, *args, **kwargs):
        """Handles POST requests to add tags to a UserTag instance."""

        encoded_data = request.POST.get("encoded_tag")

        if not encoded_data:
            return JsonResponse(
                {"error": "Invalid or corrupted tag data"}, status=400
            )

        try:
            data = json.loads(
                base64.urlsafe_b64decode(encoded_data).decode("utf-8")
            )
            try:
                user_tag = UserTag.objects.get(id=self.kwargs["pk"])
            except ObjectDoesNotExist:
                return JsonResponse({"error": "UserTag not found"}, status=404)
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
        except (json.JSONDecodeError, binascii.Error):
            logger.exception("Error decoding tag data.")
            return JsonResponse(
                {"error": "Invalid or corrupted data"}, status=400
            )
