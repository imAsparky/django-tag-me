"""tag-me model property tests - for FK lookup refactor.

Tests for the new properties added to support model rename resilience:
- TaggedFieldModel.current_model_name
- TaggedFieldModel.current_model_class
- TaggedFieldModel.app_label
- UserTag.current_model_name
- SystemTag.current_model_name

NOTE: Django's ContentType.model field stores model names in LOWERCASE.
Therefore current_model_name returns lowercase (e.g., "taggedfieldtestmodel").
Use current_model_class.__name__ if you need proper case ("TaggedFieldTestModel").
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from tag_me.models import SystemTag, TaggedFieldModel, UserTag
from tests.models import TaggedFieldTestModel

User = get_user_model()


@pytest.mark.django_db
class TestTaggedFieldModelProperties(TestCase):
    """Test new properties on TaggedFieldModel."""

    def setUp(self):
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        self.tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="StaleModelName",  # Intentionally different from actual
            field_name="test_field",
            tag_type="user",
            field_verbose_name="Test Field",
            model_verbose_name="Stale Verbose Name",
        )

    def test_current_model_name_returns_live_value(self):
        """
        current_model_name should return the live model name from ContentType,
        not the cached model_name field.

        NOTE: ContentType.model is lowercase, so current_model_name is lowercase.
        """
        # Cached value is stale
        assert self.tagged_field.model_name == "StaleModelName"

        # current_model_name returns lowercase (from ContentType.model)
        assert self.tagged_field.current_model_name == "taggedfieldtestmodel"
        # Verify it's different from the stale cached value
        assert (
            self.tagged_field.current_model_name != self.tagged_field.model_name.lower()
        )

    def test_current_model_name_after_refresh(self):
        """
        current_model_name should work correctly after refresh_from_db.
        """
        self.tagged_field.refresh_from_db()
        # ContentType.model is always lowercase
        assert self.tagged_field.current_model_name == "taggedfieldtestmodel"

    def test_current_model_class_returns_model(self):
        """
        current_model_class should return the actual Django model class.
        """
        model_class = self.tagged_field.current_model_class

        assert model_class is TaggedFieldTestModel
        # model_class._meta.model_name is also lowercase
        assert model_class._meta.model_name == "taggedfieldtestmodel"
        # But __name__ gives proper case
        assert model_class.__name__ == "TaggedFieldTestModel"

    def test_current_model_class_is_usable(self):
        """
        current_model_class should return a usable model class.
        """
        model_class = self.tagged_field.current_model_class

        # Should be able to query with it
        count = model_class.objects.count()
        assert isinstance(count, int)

        # Should be able to access meta
        assert model_class._meta.verbose_name == "Tagged Field Test Model"

    def test_app_label_property(self):
        """
        app_label should return the app label from ContentType.
        """
        assert self.tagged_field.app_label == "tests"

    def test_properties_with_select_related(self):
        """
        Properties should work correctly when content is prefetched.
        """
        # Fetch with select_related
        tagged_field = TaggedFieldModel.objects.select_related("content").get(
            pk=self.tagged_field.pk
        )

        # Properties should still work (lowercase from ContentType.model)
        assert tagged_field.current_model_name == "taggedfieldtestmodel"
        assert tagged_field.current_model_class is TaggedFieldTestModel
        assert tagged_field.app_label == "tests"

    def test_get_proper_case_name_via_model_class(self):
        """
        Demonstrate how to get proper-cased model name if needed.
        """
        # current_model_name is lowercase
        assert self.tagged_field.current_model_name == "taggedfieldtestmodel"

        # Use current_model_class.__name__ for proper case
        proper_case_name = self.tagged_field.current_model_class.__name__
        assert proper_case_name == "TaggedFieldTestModel"


@pytest.mark.django_db
class TestUserTagCurrentModelName(TestCase):
    """Test current_model_name property on UserTag."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        self.tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="SomeOldName",
            field_name="tagged_field_1",
            tag_type="user",
            field_verbose_name="Tagged Field 1",
        )

        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field,
            model_name="StaleUserTagModelName",  # Intentionally stale
            field_name="tagged_field_1",
            tags="tag1,tag2",
        )

    def test_current_model_name_via_tagged_field(self):
        """
        UserTag.current_model_name should return live value via tagged_field FK.
        """
        # Cached value is stale
        assert self.user_tag.model_name == "StaleUserTagModelName"

        # current_model_name returns lowercase via FK chain
        assert self.user_tag.current_model_name == "taggedfieldtestmodel"

    def test_current_model_name_with_select_related(self):
        """
        current_model_name should work with select_related for efficiency.
        """
        user_tag = UserTag.objects.select_related("tagged_field__content").get(
            pk=self.user_tag.pk
        )

        assert user_tag.current_model_name == "taggedfieldtestmodel"

    def test_current_model_name_when_tagged_field_none(self):
        """
        current_model_name should handle None tagged_field gracefully.
        """
        # Create UserTag without tagged_field FK (legacy data)
        user_tag_no_fk = UserTag.objects.create(
            user=self.user,
            tagged_field=None,  # No FK
            model_name="LegacyModelName",
            field_name="some_field",
            tags="tag1",
        )

        # Should fall back to cached model_name (preserves original case)
        assert user_tag_no_fk.current_model_name == "LegacyModelName"


@pytest.mark.django_db
class TestSystemTagCurrentModelName(TestCase):
    """Test current_model_name property on SystemTag."""

    def setUp(self):
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        self.tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="SomeOldName",
            field_name="tagged_field_1",
            tag_type="system",
            field_verbose_name="Tagged Field 1",
        )

        self.system_tag = SystemTag.objects.create(
            tagged_field=self.tagged_field,
            model_name="StaleSystemTagName",  # Intentionally stale
            field_name="tagged_field_1",
            tags="system_tag1,system_tag2",
        )

    def test_current_model_name_via_tagged_field(self):
        """
        SystemTag.current_model_name should return live value via tagged_field FK.
        """
        # Cached value is stale
        assert self.system_tag.model_name == "StaleSystemTagName"

        # current_model_name returns lowercase via FK chain
        assert self.system_tag.current_model_name == "taggedfieldtestmodel"

    def test_current_model_name_with_select_related(self):
        """
        current_model_name should work with select_related for efficiency.
        """
        system_tag = SystemTag.objects.select_related("tagged_field__content").get(
            pk=self.system_tag.pk
        )

        assert system_tag.current_model_name == "taggedfieldtestmodel"


@pytest.mark.django_db
class TestModelNameFieldHelpText(TestCase):
    """Test that model_name fields have appropriate help text.

    NOTE: This test requires help_text to be set on all model_name fields.
    See MODEL_CHANGES_NEEDED.md if this test fails.
    """

    def test_tagged_field_model_help_text(self):
        """
        TaggedFieldModel.model_name should have help text indicating display-only.
        """
        field = TaggedFieldModel._meta.get_field("model_name")
        help_text = field.help_text.lower() if field.help_text else ""
        assert "display" in help_text or "cache" in help_text, (
            f"TaggedFieldModel.model_name missing help_text. Got: '{field.help_text}'"
        )

    def test_user_tag_model_name_help_text(self):
        """
        UserTag.model_name should have help text indicating display-only.
        """
        field = UserTag._meta.get_field("model_name")
        help_text = field.help_text.lower() if field.help_text else ""
        assert "display" in help_text or "cache" in help_text, (
            f"UserTag.model_name missing help_text. Got: '{field.help_text}'"
        )

    def test_system_tag_model_name_help_text(self):
        """
        SystemTag.model_name should have help text indicating display-only.

        NOTE: If this fails, add help_text to SystemTag.model_name field:
        help_text="Cached model name for display. Use tagged_field FK for lookups."
        """
        field = SystemTag._meta.get_field("model_name")
        help_text = field.help_text.lower() if field.help_text else ""
        assert "display" in help_text or "cache" in help_text, (
            f"SystemTag.model_name missing help_text. Got: '{field.help_text}'. "
            f"Add: help_text='Cached model name for display. Use tagged_field FK for lookups.'"
        )
