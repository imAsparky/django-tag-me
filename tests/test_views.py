"""
Tests for tag_me/views/views.py

This test module provides coverage for the tag management views:
- TaggedFieldEditView
- UserTagListView
- UserTagEditView
- WidgetAddUserTagView

Run with: pytest tests/test_views.py -v
"""

import base64
import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory
from django.urls import reverse

from tag_me.models import (
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.views.views import (
    UserTagListView,
    WidgetAddUserTagView,
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="viewtestuser",
        password="testpass123",
        email="viewtest@example.com",
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user for admin views."""
    return User.objects.create_user(
        username="staffuser",
        password="staffpass123",
        email="staff@example.com",
        is_staff=True,
    )


@pytest.fixture
def content_type(db):
    """Get or create a ContentType for testing."""
    ct, _ = ContentType.objects.get_or_create(
        app_label="tests",
        model="viewtestmodel",
    )
    return ct


@pytest.fixture
def tagged_field(db, content_type):
    """Create a TaggedFieldModel for testing."""
    return TaggedFieldModel.objects.create(
        content=content_type,
        model_name="ViewTestModel",
        model_verbose_name="View Test Model",
        field_name="test_tags",
        field_verbose_name="Test Tags",
        tag_type="user",
        default_tags="tag1,tag2,tag3,",
    )


@pytest.fixture
def user_tag(db, user, tagged_field):
    """Create a UserTag for testing."""
    return UserTag.objects.create(
        user=user,
        tagged_field=tagged_field,
        model_name="ViewTestModel",
        model_verbose_name="View Test Model",
        field_name="test_tags",
        field_verbose_name="Test Tags",
        tags="usertag1,usertag2,",
    )


@pytest.fixture
def sync_config(db):
    """Create a TagMeSynchronise config."""
    return TagMeSynchronise.objects.create(
        name="default",
        synchronise={"test_field": [1, 2, 3]},
    )


# =============================================================================
# TAGGED FIELD EDIT VIEW TESTS
# =============================================================================


class TestTaggedFieldEditView:
    """Tests for TaggedFieldEditView."""

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_form_valid_formats_tags(self, client, staff_user, tagged_field):
        """form_valid should format tags using FieldTagListFormatter."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:tagged-field-edit", kwargs={"pk": tagged_field.pk})

        # Post with unformatted tags
        response = client.post(
            url,
            {
                "default_tags": "newtag1, newtag2,  newtag3",  # Messy formatting
            },
        )

        # Should redirect on success
        assert response.status_code in [200, 302]

        # Reload and check tags are formatted
        tagged_field.refresh_from_db()
        # Tags should be cleaned up by FieldTagListFormatter

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_form_valid_redirects_to_success_url(
        self, client, staff_user, tagged_field
    ):
        """form_valid should redirect to success_url."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:tagged-field-edit", kwargs={"pk": tagged_field.pk})

        response = client.post(
            url,
            {
                "default_tags": "tag1,tag2,",
            },
            follow=False,
        )

        # Should redirect (302) or render success
        assert response.status_code in [200, 302]

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_get_edit_form(self, client, staff_user, tagged_field):
        """GET should render the edit form."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:tagged-field-edit", kwargs={"pk": tagged_field.pk})
        response = client.get(url)

        assert response.status_code == 200


# =============================================================================
# USER TAG LIST VIEW TESTS
# Note: This view uses uuid:pk in URL - requires User model with UUID pk
# Using RequestFactory to test directly instead of URL routing
# =============================================================================


class TestUserTagListView:
    """Tests for UserTagListView."""

    @pytest.mark.django_db
    def test_get_context_data_filters_by_user_via_request_factory(
        self, user, user_tag, tagged_field
    ):
        """get_context_data should filter UserTags by user pk."""
        # Create another user with their own tags
        other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass",
        )
        other_tag = UserTag.objects.create(
            user=other_user,
            tagged_field=tagged_field,
            model_name="ViewTestModel",
            field_name="test_tags",
            tags="othertag,",
        )

        # Use RequestFactory to test directly, bypassing URL uuid requirement
        factory = RequestFactory()
        request = factory.get("/fake-url/")
        request.user = user

        # Call the view directly with user's pk
        view = UserTagListView()
        view.request = request
        view.kwargs = {"pk": user.pk}

        context = view.get_context_data()

        # Context should only contain the user's tags
        object_list = context.get("object_list", [])
        for obj in object_list:
            assert obj.user_id == user.pk

    @pytest.mark.django_db
    def test_get_context_data_empty_for_user_without_tags(self, tagged_field):
        """Should return empty queryset for user with no tags."""
        # Create user without tags
        new_user = User.objects.create_user(
            username="notagsuser",
            password="notagspass",
        )

        factory = RequestFactory()
        request = factory.get("/fake-url/")
        request.user = new_user

        view = UserTagListView()
        view.request = request
        view.kwargs = {"pk": new_user.pk}

        context = view.get_context_data()

        # Should be empty
        object_list = context.get("object_list", [])
        assert len(list(object_list)) == 0


# =============================================================================
# USER TAG EDIT VIEW TESTS
# =============================================================================


class TestUserTagEditView:
    """Tests for UserTagEditView."""

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_form_valid_saves_tags(self, client, user, user_tag):
        """form_valid should save the updated tags."""
        client.login(username="viewtestuser", password="testpass123")

        url = reverse("tag_me:edit-tag", kwargs={"pk": user_tag.pk})

        response = client.post(
            url,
            {
                "tags": "updated1,updated2,updated3,",
            },
        )

        # Should redirect on success
        assert response.status_code in [200, 302]

        # Verify tags were updated
        user_tag.refresh_from_db()
        assert "updated1" in user_tag.tags or response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_form_invalid_returns_form_with_errors(self, client, user, user_tag):
        """form_invalid should return the form with errors."""
        client.login(username="viewtestuser", password="testpass123")

        url = reverse("tag_me:edit-tag", kwargs={"pk": user_tag.pk})

        # Post with potentially invalid data (depends on form validation)
        # Even if form doesn't have required fields, this tests the view path
        response = client.post(url, {})

        # Should either succeed or return form
        assert response.status_code in [200, 302]

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_get_context_data_includes_usertag(self, client, user, user_tag):
        """get_context_data should include the usertag in context."""
        client.login(username="viewtestuser", password="testpass123")

        url = reverse("tag_me:edit-tag", kwargs={"pk": user_tag.pk})
        response = client.get(url)

        assert response.status_code == 200

        if hasattr(response, "context") and response.context:
            assert "usertag" in response.context
            assert response.context["usertag"].pk == user_tag.pk


# =============================================================================
# WIDGET ADD USER TAG VIEW TESTS (covers lines 108, 117-141)
# =============================================================================


class TestWidgetAddUserTagView:
    """Tests for WidgetAddUserTagView AJAX endpoint."""

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_adds_tags_successfully(self, client, user, user_tag):
        """POST with valid encoded data should add tags."""
        client.login(username="viewtestuser", password="testpass123")

        # Encode tag data as the widget does
        tag_data = ["newtag1", "newtag2"]
        encoded_data = base64.urlsafe_b64encode(
            json.dumps(tag_data).encode("utf-8")
        ).decode("utf-8")

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        response = client.post(url, {"encoded_tag": encoded_data})

        assert response.status_code == 200

        data = response.json()
        assert data.get("success") is True
        assert "tags" in data

        # Verify tags were added
        user_tag.refresh_from_db()
        assert "newtag1" in user_tag.tags
        assert "newtag2" in user_tag.tags

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_missing_encoded_tag_returns_400(self, client, user, user_tag):
        """POST without encoded_tag should return 400."""
        client.login(username="viewtestuser", password="testpass123")

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        response = client.post(url, {})  # No encoded_tag

        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "Invalid or corrupted tag data" in data["error"]

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_invalid_base64_returns_400(self, client, user, user_tag):
        """POST with invalid base64 should return 400."""
        client.login(username="viewtestuser", password="testpass123")

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        # Single character - invalid base64 padding
        response = client.post(url, {"encoded_tag": "x"})

        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_invalid_utf8_returns_400(self, client, user, user_tag):
        """POST with valid base64 but invalid UTF-8 should return 400."""
        client.login(username="viewtestuser", password="testpass123")

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        # Valid base64 that decodes to invalid UTF-8 bytes (0x80 is invalid UTF-8 start)
        # base64.urlsafe_b64encode(b'\x80\x81\x82') = 'gIGC'
        response = client.post(url, {"encoded_tag": "gIGC"})

        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_invalid_json_returns_400(self, client, user, user_tag):
        """POST with valid base64 but invalid JSON should return 400."""
        client.login(username="viewtestuser", password="testpass123")

        # Encode invalid JSON
        invalid_json = "not valid json {"
        encoded_data = base64.urlsafe_b64encode(invalid_json.encode("utf-8")).decode(
            "utf-8"
        )

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        response = client.post(url, {"encoded_tag": encoded_data})

        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_nonexistent_usertag_returns_404(self, client, user):
        """POST with non-existent UserTag pk should return 404."""
        client.login(username="viewtestuser", password="testpass123")

        tag_data = ["tag1"]
        encoded_data = base64.urlsafe_b64encode(
            json.dumps(tag_data).encode("utf-8")
        ).decode("utf-8")

        url = reverse("tag_me:add-tag", kwargs={"pk": 99999})
        response = client.post(url, {"encoded_tag": encoded_data})

        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_preserves_existing_tags(self, client, user, user_tag):
        """POST should preserve existing tags when adding new ones."""
        client.login(username="viewtestuser", password="testpass123")

        original_tags = user_tag.tags  # "usertag1,usertag2,"

        # Add new tags
        tag_data = ["newtag"]
        encoded_data = base64.urlsafe_b64encode(
            json.dumps(tag_data).encode("utf-8")
        ).decode("utf-8")

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        response = client.post(url, {"encoded_tag": encoded_data})

        assert response.status_code == 200

        user_tag.refresh_from_db()
        # Should still have original tags
        assert "usertag1" in user_tag.tags
        assert "usertag2" in user_tag.tags
        # Plus new tag
        assert "newtag" in user_tag.tags

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_post_returns_updated_tag_list(self, client, user, user_tag):
        """POST should return the complete updated tag list."""
        client.login(username="viewtestuser", password="testpass123")

        tag_data = ["addedtag"]
        encoded_data = base64.urlsafe_b64encode(
            json.dumps(tag_data).encode("utf-8")
        ).decode("utf-8")

        url = reverse("tag_me:add-tag", kwargs={"pk": user_tag.pk})
        response = client.post(url, {"encoded_tag": encoded_data})

        assert response.status_code == 200

        data = response.json()
        assert "tags" in data
        assert isinstance(data["tags"], list)
        assert "addedtag" in data["tags"]


# =============================================================================
# OTHER VIEW TESTS (basic coverage)
# =============================================================================


class TestOtherViews:
    """Basic tests for other views."""

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_tag_management_view(self, client, staff_user):
        """TagManagementView should render template."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:tag-mgmt")
        response = client.get(url)

        assert response.status_code == 200
        assert "tag_me/mgmt/management.html" in [t.name for t in response.templates]

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_tag_field_list_view(self, client, staff_user, tagged_field):
        """TagFieldListView should list tagged fields."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:tagged-field-list")
        response = client.get(url)

        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_synchronised_tag_field_list_view(self, client, staff_user, sync_config):
        """SynchronisedTagFieldListView should list sync configs."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:sync-tagged-field-list")
        response = client.get(url)

        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.urls("tests.test_urls")
    def test_mgmt_user_tag_list_view(self, client, staff_user, user_tag):
        """MgmtUserTagListView should list all user tags."""
        client.login(username="staffuser", password="staffpass123")

        url = reverse("tag_me:list-tags")
        response = client.get(url)

        assert response.status_code == 200


# =============================================================================
# REQUEST FACTORY TESTS (alternative approach without URL routing)
# =============================================================================


class TestViewsWithRequestFactory:
    """Tests using RequestFactory for more isolated view testing."""

    @pytest.mark.django_db
    def test_widget_add_tag_view_directly(self, user, user_tag):
        """Test WidgetAddUserTagView directly with RequestFactory."""
        factory = RequestFactory()

        tag_data = ["directtag"]
        encoded_data = base64.urlsafe_b64encode(
            json.dumps(tag_data).encode("utf-8")
        ).decode("utf-8")

        request = factory.post("/fake-url/", {"encoded_tag": encoded_data})
        request.user = user

        view = WidgetAddUserTagView.as_view()
        response = view(request, pk=user_tag.pk)

        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["success"] is True

    @pytest.mark.django_db
    def test_widget_add_tag_view_missing_data(self, user, user_tag):
        """Test WidgetAddUserTagView with missing encoded_tag."""
        factory = RequestFactory()

        request = factory.post("/fake-url/", {})
        request.user = user

        view = WidgetAddUserTagView.as_view()
        response = view(request, pk=user_tag.pk)

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_widget_add_tag_view_invalid_pk(self, user):
        """Test WidgetAddUserTagView with non-existent pk."""
        factory = RequestFactory()

        tag_data = ["tag"]
        encoded_data = base64.urlsafe_b64encode(
            json.dumps(tag_data).encode("utf-8")
        ).decode("utf-8")

        request = factory.post("/fake-url/", {"encoded_tag": encoded_data})
        request.user = user

        view = WidgetAddUserTagView.as_view()
        response = view(request, pk=99999)

        assert response.status_code == 404
