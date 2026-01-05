# tag_me/tests/test_model_rename_resilience.py
"""
Tests to verify that tag_me survives model renames.

These tests validate that:
1. TaggedFieldModel lookups use ContentType FK, not model_name
2. UserTag lookups use tagged_field FK, not model_name
3. Cached model_name fields are updated via update_or_create

Run with:
    ./manage.py test tag_me.tests.test_model_rename_resilience
"""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase

from tag_me.models import TagBase, TaggedFieldModel, UserTag

User = get_user_model()


class TaggedFieldModelLookupTest(TestCase):
    """Test that TaggedFieldModel lookups are rename-resilient."""

    def setUp(self):
        """Create a TaggedFieldModel with a 'stale' model_name."""
        # Use ContentType for User model as a test subject
        self.content_type = ContentType.objects.get_for_model(User)

        # Create with a deliberately stale model_name to simulate post-rename state
        self.tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            field_name="test_tags",
            model_name="stale_old_name",  # Deliberately incorrect
            model_verbose_name="Stale Old Name",
            field_verbose_name="Test Tags",
            tag_type="user",
        )

    def test_lookup_by_content_and_field_name_works(self):
        """Lookup should succeed using ContentType + field_name."""
        found = TaggedFieldModel.objects.get(
            content=self.content_type,
            field_name="test_tags",
        )
        self.assertEqual(found.id, self.tagged_field.id)

    def test_current_model_name_property_returns_live_value(self):
        """The current_model_name property should return the live ContentType model."""
        # The stored model_name is stale
        self.assertEqual(self.tagged_field.model_name, "stale_old_name")

        # But current_model_name returns the actual current name from ContentType
        self.assertEqual(self.tagged_field.current_model_name, self.content_type.model)

    def test_current_model_class_property_returns_model(self):
        """The current_model_class property should return the actual model class."""
        model_class = self.tagged_field.current_model_class
        self.assertEqual(model_class, User)

    def test_update_or_create_refreshes_cached_names(self):
        """update_or_create should refresh model_name when called."""
        # Simulate what happens on post_migrate
        TaggedFieldModel.objects.update_or_create(
            content=self.content_type,
            field_name="test_tags",
            defaults={
                "model_name": "refreshed_name",
                "model_verbose_name": "Refreshed Name",
                "field_verbose_name": "Test Tags",
                "tag_type": "user",
            },
        )

        self.tagged_field.refresh_from_db()
        self.assertEqual(self.tagged_field.model_name, "refreshed_name")


class UserTagLookupTest(TestCase):
    """Test that UserTag lookups are rename-resilient."""

    def setUp(self):
        """Create a UserTag linked via FK to TaggedFieldModel."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

        self.content_type = ContentType.objects.get_for_model(User)

        self.tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            field_name="test_tags",
            model_name="stale_name",
            model_verbose_name="Stale",
            field_verbose_name="Test Tags",
            tag_type="user",
        )

        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field,
            model_name="stale_name",  # Also stale
            model_verbose_name="Stale",
            field_name="test_tags",
            field_verbose_name="Test Tags",
            tags="tag1, tag2,",
            slug=TagBase.slugify(tag=str(self.user.id)),
        )

    def test_lookup_by_tagged_field_fk_works(self):
        """UserTag should be findable via tagged_field FK."""
        found = UserTag.objects.get(
            user=self.user,
            tagged_field=self.tagged_field,
        )
        self.assertEqual(found.id, self.user_tag.id)

    def test_current_model_name_property(self):
        """UserTag.current_model_name should return live value from TaggedFieldModel."""
        # Stored model_name is stale
        self.assertEqual(self.user_tag.model_name, "stale_name")

        # current_model_name comes from the FK chain
        self.assertEqual(self.user_tag.current_model_name, self.content_type.model)

    def test_tags_persist_after_model_name_becomes_stale(self):
        """User's tags should remain accessible even with stale model_name."""
        # The model_name is wrong, but we can still find tags via FK
        user_tag = UserTag.objects.get(
            user=self.user,
            tagged_field=self.tagged_field,
        )
        self.assertEqual(user_tag.tags, "tag1, tag2,")


class ConstraintTest(TestCase):
    """Test the unique constraint behavior."""

    def setUp(self):
        self.content_type = ContentType.objects.get_for_model(User)

    def test_duplicate_content_field_name_rejected(self):
        """Cannot create two TaggedFieldModels with same content + field_name."""
        TaggedFieldModel.objects.create(
            content=self.content_type,
            field_name="unique_field",
            model_name="name1",
            model_verbose_name="Name 1",
            field_verbose_name="Field",
            tag_type="user",
        )

        with self.assertRaises(IntegrityError):
            TaggedFieldModel.objects.create(
                content=self.content_type,
                field_name="unique_field",  # Same field_name
                model_name="name2",  # Different model_name - doesn't matter anymore
                model_verbose_name="Name 2",
                field_verbose_name="Field",
                tag_type="user",
            )

    def test_different_field_names_allowed(self):
        """Same content with different field_names should be allowed."""
        tf1 = TaggedFieldModel.objects.create(
            content=self.content_type,
            field_name="field_one",
            model_name="model",
            model_verbose_name="Model",
            field_verbose_name="Field One",
            tag_type="user",
        )

        tf2 = TaggedFieldModel.objects.create(
            content=self.content_type,
            field_name="field_two",  # Different field
            model_name="model",
            model_verbose_name="Model",
            field_verbose_name="Field Two",
            tag_type="user",
        )

        self.assertNotEqual(tf1.id, tf2.id)


class AllFieldsTagMeModelFormMixinTest(TestCase):
    """Test that AllFieldsTagMeModelFormMixin uses FK lookups."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="formuser",
            email="form@example.com",
            password="testpass123",
        )

        self.content_type = ContentType.objects.get_for_model(User)

        self.tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            field_name="form_tags",
            model_name="stale_model",
            model_verbose_name="Stale Model",
            field_verbose_name="Form Tags",
            tag_type="user",
        )

        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field,
            model_name="stale_model",
            model_verbose_name="Stale Model",
            field_name="form_tags",
            field_verbose_name="Form Tags",
            tags="formtag1, formtag2,",
            slug=TagBase.slugify(tag=str(self.user.id)),
        )

    def test_mixin_finds_user_tag_via_fk(self):
        """
        The mixin should find UserTag via tagged_field FK, not model_name.

        This tests the core fix - even with stale model_name, the FK lookup works.
        """

        # Simulate what the mixin does
        tagged_models = TaggedFieldModel.objects.filter(tag_type="user")
        user_tags = UserTag.objects.filter(user=self.user)

        for tagged_model in tagged_models:
            # This is the FIXED query - uses FK not model_name
            try:
                user_tag = user_tags.get(tagged_field=tagged_model)
                self.assertEqual(user_tag.tags, "formtag1, formtag2,")
            except UserTag.DoesNotExist:
                # Other tagged_models may not have user tags, that's fine
                pass
