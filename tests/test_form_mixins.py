"""tag-me form mixin tests - UPDATED for FK lookup refactor.

Changes:
1. AllFieldsTagMeModelFormMixin tests now verify FK lookup (tagged_field=) instead of model_name lookup
2. Added test for stale model_name resilience
3. Added test for select_related optimization
"""

import logging

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.test import TestCase

from tag_me.forms.fields import TagMeCharField
from tag_me.forms.mixins import (
    AllFieldsTagMeModelFormMixin,
    TagMeModelFormMixin,
)
from tag_me.models import (
    TaggedFieldModel,
    UserTag,
)
from tag_me.widgets import TagMeSelectMultipleWidget
from tests.models import TaggedFieldTestModel

logger = logging.getLogger(__name__)

User = get_user_model()


class TestTagMeModelFormMixin(TestCase):
    """Test the TagMeModelFormMixin"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.tagged_model = TaggedFieldTestModel.objects.create(
            tagged_field_1="tag1,tag2", tagged_field_2="tag3,tag4"
        )

        # Create test forms dynamically in setUp to avoid database access during module import
        class TaggedFieldTestForm(TagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1", "tagged_field_2"]

        self.TaggedFieldTestForm = TaggedFieldTestForm

    def test_initialization_with_user(self):
        """Test form initialization with user parameter"""
        form = self.TaggedFieldTestForm(user=self.user)
        self.assertEqual(form.user, self.user)

    def test_initialization_without_user(self):
        """Test form initialization without user parameter"""
        form = self.TaggedFieldTestForm()
        self.assertIsNone(form.user)

    def test_tagme_field_widget_attributes(self):
        """Test that TagMeCharField widgets get proper attributes"""
        form = self.TaggedFieldTestForm(user=self.user)

        # Test both TagMeCharFields
        for field_name in ["tagged_field_1", "tagged_field_2"]:
            field = form.fields[field_name]
            self.assertIsInstance(field, TagMeCharField)
            self.assertEqual(field.widget.attrs["css_class"], "")
            self.assertEqual(field.widget.attrs["user"], self.user)

    def test_model_obj_handling(self):
        """Test form initialization with model_obj parameter"""
        form = self.TaggedFieldTestForm(model_obj=self.tagged_model)
        self.assertEqual(form.model_obj, self.tagged_model)

    def test_form_with_instance(self):
        """Test form initialization with an instance"""
        form = self.TaggedFieldTestForm(instance=self.tagged_model, user=self.user)
        self.assertEqual(form.initial["tagged_field_1"], "tag1,tag2")
        self.assertEqual(form.initial["tagged_field_2"], "tag3,tag4")


class TestAllFieldsTagMeModelFormMixin(TestCase):
    """Test the AllFieldsTagMeModelFormMixin - UPDATED for FK lookup"""

    def setUp(self):
        # Create test user with unique username
        self.user = User.objects.create_user(
            username="alltags_testuser", password="testpass"
        )

        # Get content type for our test model
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create TaggedFieldModel entry - all required fields
        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name=TaggedFieldTestModel._meta.object_name,
            model_verbose_name=str(TaggedFieldTestModel._meta.verbose_name),
            field_name="tagged_field_1",
            tag_type="user",
            field_verbose_name="Tagged Field 1",
        )

        # Create UserTag with tagged_field FK - THIS IS CRITICAL
        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,  # FK reference
            model_name=TaggedFieldTestModel._meta.object_name,
            model_verbose_name=str(TaggedFieldTestModel._meta.verbose_name),
            field_name="tagged_field_1",
            field_verbose_name="Tagged Field 1",
            tags="tag1,tag2,tag3",
        )

        # Create test form
        class AllFieldsTaggedTestForm(AllFieldsTagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1"]

        self.AllFieldsTaggedTestForm = AllFieldsTaggedTestForm

    def test_setup_data_exists(self):
        """Diagnostic test: Verify test data is correctly created."""
        # Verify TaggedFieldModel exists
        tfm_count = TaggedFieldModel.objects.filter(tag_type="user").count()
        assert tfm_count >= 1, (
            f"Expected at least 1 TaggedFieldModel, found {tfm_count}"
        )

        # Verify our specific TaggedFieldModel
        tfm = TaggedFieldModel.objects.filter(
            content=self.content_type,
            field_name="tagged_field_1",
            tag_type="user",
        ).first()
        assert tfm is not None, "TaggedFieldModel not found for tagged_field_1"
        assert tfm.pk == self.tagged_field_model.pk

        # Verify UserTag exists with FK
        ut = UserTag.objects.filter(
            user=self.user,
            tagged_field=self.tagged_field_model,
        ).first()
        assert ut is not None, (
            f"UserTag not found. "
            f"UserTags for user: {list(UserTag.objects.filter(user=self.user).values('id', 'tagged_field_id', 'field_name'))}"
        )
        assert ut.tagged_field_id == self.tagged_field_model.pk, (
            f"UserTag.tagged_field_id mismatch: {ut.tagged_field_id} != {self.tagged_field_model.pk}"
        )
        assert ut.tags == "tag1,tag2,tag3"

    def test_mixin_query_logic(self):
        """Diagnostic test: Verify mixin query logic works."""
        # Simulate what the mixin does
        tagged_models = TaggedFieldModel.objects.filter(tag_type="user")
        assert tagged_models.exists(), "No TaggedFieldModel with tag_type='user' found"

        user_tags = UserTag.objects.filter(user=self.user).select_related(
            "tagged_field"
        )
        assert user_tags.exists(), f"No UserTag found for user {self.user}"

        # Try the exact lookup the mixin uses
        for tagged_model in tagged_models:
            try:
                user_tag = user_tags.get(tagged_field=tagged_model)
                # Found it - this is what should happen
                assert user_tag.tags == "tag1,tag2,tag3", (
                    f"Tags mismatch: {user_tag.tags}"
                )
                return  # Success
            except ObjectDoesNotExist:
                continue

        # If we get here, no match was found
        pytest.fail(
            f"Mixin query logic failed. "
            f"TaggedFieldModels (tag_type=user): {list(tagged_models.values('id', 'field_name', 'content_id'))}. "
            f"UserTags: {list(user_tags.values('id', 'tagged_field_id', 'field_name'))}."
        )

    def test_widget_creation(self):
        """Test that the correct widget is created with proper configuration"""
        form = self.AllFieldsTaggedTestForm(user=self.user)

        # Check field exists
        assert "tagged_field_1" in form.fields, (
            f"Field 'tagged_field_1' not in form.fields. "
            f"Available fields: {list(form.fields.keys())}"
        )

        field = form.fields["tagged_field_1"]

        # Check widget type
        assert isinstance(field.widget, TagMeSelectMultipleWidget), (
            f"Expected TagMeSelectMultipleWidget, got {type(field.widget).__name__}. "
            f"This means _create_dynamic_tagme_fields() didn't replace the field. "
            f"Check that TaggedFieldModel and UserTag are correctly linked via FK."
        )

        # Verify widget attributes - strict assertions
        widget_attrs = field.widget.attrs
        assert "all_tag_fields_mixin" in widget_attrs, (
            f"'all_tag_fields_mixin' not in widget attrs. Attrs: {widget_attrs}"
        )
        assert widget_attrs["all_tag_fields_mixin"] is True
        assert widget_attrs["display_all_tags"] is False
        assert widget_attrs["user"] == self.user
        assert widget_attrs["all_tag_fields_tag_string"] == "tag1,tag2,tag3"

    def test_missing_user_tag(self):
        """Test behavior when UserTag doesn't exist for a field"""
        # Delete the UserTag
        self.user_tag.delete()

        form = self.AllFieldsTaggedTestForm(user=self.user)

        # Field should remain as original TagMeCharField (mixin didn't find UserTag to replace it)
        field = form.fields["tagged_field_1"]
        assert isinstance(field, TagMeCharField), (
            f"Expected TagMeCharField when UserTag missing, got {type(field).__name__}"
        )

    def test_no_user_provided(self):
        """Test that form requires a user"""
        with pytest.raises(ObjectDoesNotExist):
            self.AllFieldsTaggedTestForm()

    # =====================================================
    # NEW TESTS FOR FK LOOKUP REFACTOR
    # =====================================================

    def test_fk_lookup_works_with_stale_model_name(self):
        """
        Test that FK lookup works even when model_name is stale.

        This is the KEY TEST for the refactor - proves that lookups use
        tagged_field FK, not model_name string.
        """
        # Simulate a stale model_name (as if model was renamed)
        self.tagged_field_model.model_name = "OldModelName"
        self.tagged_field_model.save()

        # Also update UserTag's cached model_name to be stale
        self.user_tag.model_name = "OldModelName"
        self.user_tag.save()

        # Form should still work because mixin uses tagged_field FK
        form = self.AllFieldsTaggedTestForm(user=self.user)

        field = form.fields["tagged_field_1"]
        assert isinstance(field.widget, TagMeSelectMultipleWidget), (
            "Widget should be customized even with stale model_name - "
            "this proves FK lookup is working"
        )

        # Tags should still be found via FK lookup
        widget_attrs = field.widget.attrs
        assert widget_attrs["all_tag_fields_tag_string"] == "tag1,tag2,tag3", (
            "Tags should be retrieved via FK lookup, not model_name lookup"
        )

    def test_query_uses_select_related(self):
        """Test that the mixin uses select_related for performance."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            form = self.AllFieldsTaggedTestForm(user=self.user)
            _ = form.fields["tagged_field_1"]

        queries = [q["sql"] for q in context.captured_queries]
        # Table name is tag_me_usertag, not user_tag
        user_tag_queries = [q for q in queries if "tag_me_usertag" in q.lower()]

        assert len(user_tag_queries) >= 1, (
            f"Expected UserTag query, got queries: {queries}"
        )

        # Verify select_related is working - should see JOIN in the query
        joined_queries = [q for q in user_tag_queries if "join" in q.lower()]
        assert len(joined_queries) >= 1, (
            f"Expected JOIN (select_related), got queries: {user_tag_queries}"
        )

    def test_lookup_by_tagged_field_not_model_name(self):
        """Verify the mixin queries by tagged_field FK, not by model_name."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            form = self.AllFieldsTaggedTestForm(user=self.user)
            _ = form.fields["tagged_field_1"]

        queries = [q["sql"] for q in context.captured_queries]
        # Table name is tag_me_usertag
        user_tag_queries = [q for q in queries if "tag_me_usertag" in q.lower()]

        # Verify FK lookup is used (tagged_field_id in WHERE clause)
        for query in user_tag_queries:
            query_lower = query.lower()
            if "where" in query_lower:
                # Should use tagged_field_id for the lookup
                assert "tagged_field_id" in query_lower, (
                    f"Query should use tagged_field_id FK: {query}"
                )


class TestUserTagFKSync(TestCase):
    """
    Test UserTag.save() sync logic uses FK lookup.

    NEW TEST CLASS for the refactor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser3", password="testpass")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name=TaggedFieldTestModel._meta.object_name,
            model_verbose_name=str(TaggedFieldTestModel._meta.verbose_name),
            field_name="tagged_field_1",
            tag_type="user",
            field_verbose_name="Tagged Field 1",
        )

    def test_user_tag_sync_with_stale_model_name(self):
        """
        Test that UserTag.save() sync works even with stale model_name.

        The sync should find TaggedFieldModel via content FK, not model_name.
        """
        # Create UserTag with tagged_field FK
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            model_name=TaggedFieldTestModel._meta.object_name,
            field_name="tagged_field_1",
            tags="initial_tag",
        )

        # Simulate stale model_name
        self.tagged_field_model.model_name = "OldModelName"
        self.tagged_field_model.save()

        user_tag.model_name = "OldModelName"
        user_tag.save()

        # Update tags - this triggers the sync logic
        user_tag.tags = "updated_tag"
        user_tag.save()

        # Refresh and verify sync still worked
        user_tag.refresh_from_db()
        assert user_tag.tags == "updated_tag"

        # The tagged_field FK should still be valid
        assert user_tag.tagged_field == self.tagged_field_model
