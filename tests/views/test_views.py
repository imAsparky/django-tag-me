"""
Tests for tag_me/views/views.py

Covers:
    - TagManagementView: template rendering
    - TagFieldListView: tagged field listing
    - SynchronisedTagFieldListView: sync config listing
    - TaggedFieldEditView: form_valid tag formatting, GET
    - UserTagListView: context filtering by user pk
    - UserTagEditView: form_valid save, context includes usertag
    - MgmtUserTagListView: admin tag listing
    - WidgetAddUserTagView: add tags via AJAX, error handling (400/404),
      tag preservation, response format

Requires: tests.test_urls providing ROOT_URLCONF with tag_me URL patterns.

Run with: pytest tests/test_views.py -v
"""

import base64
import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse

from tag_me.models import (
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.views.views import UserTagListView

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def view_user(db):
    """User for view tests — saved to DB so login works."""
    return User.objects.create_user(
        username="viewtestuser",
        password="testpass123",
        email="viewtest@example.com",
    )


@pytest.fixture
def staff_user(db):
    """Staff user for admin views."""
    return User.objects.create_user(
        username="staffuser",
        password="staffpass123",
        email="staff@example.com",
        is_staff=True,
    )


@pytest.fixture
def view_content_type(db):
    """Fake ContentType for view test isolation."""
    ct, _ = ContentType.objects.get_or_create(app_label="tests", model="viewtestmodel")
    return ct


@pytest.fixture
def view_tagged_field(db, view_content_type):
    """TaggedFieldModel for view tests."""
    return TaggedFieldModel.objects.create(
        content=view_content_type,
        model_name="ViewTestModel",
        model_verbose_name="View Test Model",
        field_name="test_tags",
        field_verbose_name="Test Tags",
        tag_type="user",
        default_tags="tag1,tag2,tag3,",
    )


@pytest.fixture
def view_user_tag(db, view_user, view_tagged_field):
    """UserTag for view tests."""
    return UserTag.objects.create(
        user=view_user,
        tagged_field=view_tagged_field,
        model_name="ViewTestModel",
        model_verbose_name="View Test Model",
        field_name="test_tags",
        field_verbose_name="Test Tags",
        tags="usertag1,usertag2,",
    )


@pytest.fixture
def view_sync_config(db):
    """TagMeSynchronise config for sync list view."""
    obj, _ = TagMeSynchronise.objects.get_or_create(
        name="default",
        defaults={"synchronise": {"test_field": [1, 2, 3]}},
    )
    return obj


def _encode_tag_data(tags):
    """Encode tag data the way the widget does."""
    return base64.urlsafe_b64encode(json.dumps(tags).encode("utf-8")).decode("utf-8")


# =============================================================================
# Management & List Views
# =============================================================================


@pytest.mark.django_db
@pytest.mark.urls("tests.test_urls")
class TestManagementViews:
    """Basic rendering tests for management/list views."""

    def test_tag_management_view(self, client, staff_user):
        client.login(username="staffuser", password="staffpass123")
        url = reverse("tag_me:tag-mgmt")
        response = client.get(url)

        assert response.status_code == 200
        template_names = [t.name for t in response.templates]
        assert "tag_me/mgmt/management.html" in template_names

    def test_tag_field_list_view(self, client, staff_user, view_tagged_field):
        client.login(username="staffuser", password="staffpass123")
        url = reverse("tag_me:tagged-field-list")
        response = client.get(url)

        assert response.status_code == 200

    def test_synchronised_tag_field_list_view(
        self, client, staff_user, view_sync_config
    ):
        client.login(username="staffuser", password="staffpass123")
        url = reverse("tag_me:sync-tagged-field-list")
        response = client.get(url)

        assert response.status_code == 200

    def test_mgmt_user_tag_list_view(self, client, staff_user, view_user_tag):
        client.login(username="staffuser", password="staffpass123")
        url = reverse("tag_me:list-tags")
        response = client.get(url)

        assert response.status_code == 200


# =============================================================================
# TaggedFieldEditView
# =============================================================================


@pytest.mark.django_db
@pytest.mark.urls("tests.test_urls")
class TestTaggedFieldEditView:
    """Tests for TaggedFieldEditView."""

    def test_get_renders_form(self, client, staff_user, view_tagged_field):
        client.login(username="staffuser", password="staffpass123")
        url = reverse("tag_me:tagged-field-edit", kwargs={"pk": view_tagged_field.pk})
        response = client.get(url)

        assert response.status_code == 200

    def test_form_valid_formats_tags(self, client, staff_user, view_tagged_field):
        """form_valid should format tags using FieldTagListFormatter."""
        client.login(username="staffuser", password="staffpass123")
        url = reverse("tag_me:tagged-field-edit", kwargs={"pk": view_tagged_field.pk})

        response = client.post(
            url, {"default_tags": "newtag1, newtag2,  newtag3"}, follow=False
        )

        # UpdateView redirects on success
        assert response.status_code == 302

        view_tagged_field.refresh_from_db()
        # Tags should be cleaned up by FieldTagListFormatter
        assert "newtag1" in view_tagged_field.default_tags


# =============================================================================
# UserTagListView (uses RequestFactory — URL requires uuid pk)
# =============================================================================


@pytest.mark.django_db
class TestUserTagListView:
    """Tests for UserTagListView using RequestFactory."""

    def test_filters_by_user_pk(self, view_user, view_user_tag, view_tagged_field):
        other_user = User.objects.create_user(username="otheruser", password="pass")
        UserTag.objects.create(
            user=other_user,
            tagged_field=view_tagged_field,
            model_name="ViewTestModel",
            field_name="test_tags",
            tags="othertag,",
        )

        factory = RequestFactory()
        request = factory.get("/fake-url/")
        request.user = view_user

        view = UserTagListView()
        view.request = request
        view.kwargs = {"pk": view_user.pk}

        context = view.get_context_data()
        object_list = list(context.get("object_list", []))

        assert len(object_list) > 0
        for obj in object_list:
            assert obj.user_id == view_user.pk

    def test_empty_for_user_without_tags(self, view_tagged_field):
        new_user = User.objects.create_user(username="notagsuser", password="pass")

        factory = RequestFactory()
        request = factory.get("/fake-url/")
        request.user = new_user

        view = UserTagListView()
        view.request = request
        view.kwargs = {"pk": new_user.pk}

        context = view.get_context_data()
        object_list = list(context.get("object_list", []))

        assert len(object_list) == 0


# =============================================================================
# UserTagEditView
# =============================================================================


@pytest.mark.django_db
@pytest.mark.urls("tests.test_urls")
class TestUserTagEditView:
    """Tests for UserTagEditView."""

    def test_get_includes_usertag_in_context(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:edit-tag", kwargs={"pk": view_user_tag.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "usertag" in response.context
        assert response.context["usertag"].pk == view_user_tag.pk

    def test_form_valid_saves_tags(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:edit-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(
            url, {"tags": "updated1,updated2,updated3,"}, follow=False
        )

        assert response.status_code == 302

        view_user_tag.refresh_from_db()
        assert "updated1" in view_user_tag.tags

    def test_form_invalid_returns_form(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:edit-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(url, {})

        # Should re-render form (200) or redirect (302) depending on form validation
        assert response.status_code in [200, 302]


# =============================================================================
# WidgetAddUserTagView (AJAX endpoint)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.urls("tests.test_urls")
class TestWidgetAddUserTagView:
    """Tests for WidgetAddUserTagView POST endpoint."""

    def test_adds_tags_successfully(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(
            url, {"encoded_tag": _encode_tag_data(["newtag1", "newtag2"])}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tags" in data
        assert isinstance(data["tags"], list)

        view_user_tag.refresh_from_db()
        assert "newtag1" in view_user_tag.tags
        assert "newtag2" in view_user_tag.tags

    def test_preserves_existing_tags(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(url, {"encoded_tag": _encode_tag_data(["newtag"])})

        assert response.status_code == 200

        view_user_tag.refresh_from_db()
        assert "usertag1" in view_user_tag.tags
        assert "usertag2" in view_user_tag.tags
        assert "newtag" in view_user_tag.tags

    def test_returns_updated_tag_list(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(url, {"encoded_tag": _encode_tag_data(["addedtag"])})

        data = response.json()
        assert "addedtag" in data["tags"]

    def test_missing_encoded_tag_returns_400(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(url, {})

        assert response.status_code == 400
        assert "error" in response.json()

    def test_invalid_base64_returns_400(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": view_user_tag.pk})

        response = client.post(url, {"encoded_tag": "x"})

        assert response.status_code == 400
        assert "error" in response.json()

    def test_invalid_json_returns_400(self, client, view_user, view_user_tag):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": view_user_tag.pk})

        encoded = base64.urlsafe_b64encode(b"not valid json {").decode("utf-8")
        response = client.post(url, {"encoded_tag": encoded})

        assert response.status_code == 400
        assert "error" in response.json()

    def test_nonexistent_usertag_returns_404(self, client, view_user):
        client.login(username="viewtestuser", password="testpass123")
        url = reverse("tag_me:add-tag", kwargs={"pk": 99999})

        response = client.post(url, {"encoded_tag": _encode_tag_data(["tag1"])})

        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()
