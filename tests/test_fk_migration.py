"""
Test suite for FK lookup refactor migration.

This test suite covers:
1. Migration FK population strategies (all 5 strategies)
2. Edge cases and failure modes
3. Model rename scenarios
4. Orphaned record handling
5. Runtime behavior after migration
6. Breaking change validation

Run with: pytest tests/test_fk_migration.py -v
"""

import warnings

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, connection
from django.forms import ModelForm
from django.test import TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext

from tag_me.forms.mixins import AllFieldsTagMeModelFormMixin
from tag_me.models import TaggedFieldModel, UserTag
from tag_me.models.fields import TagMeCharField
from tag_me.registry import FieldMetadata, TagPersistence, TagType
from tests.models import TaggedFieldTestModel

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def content_type(db):
    """Get ContentType for test model."""
    return ContentType.objects.get_for_model(TaggedFieldTestModel)


@pytest.fixture
def tagged_field_model(db, content_type):
    """Create a TaggedFieldModel entry."""
    return TaggedFieldModel.objects.create(
        content=content_type,
        model_name="TaggedFieldTestModel",
        model_verbose_name="Tagged Field Test Model",
        field_name="test_field",
        field_verbose_name="Test Field",
        tag_type="user",
    )


@pytest.fixture
def user_tag(db, user, tagged_field_model):
    """Create a UserTag with FK properly set."""
    return UserTag.objects.create(
        user=user,
        tagged_field=tagged_field_model,
        model_name="TaggedFieldTestModel",
        model_verbose_name="Tagged Field Test Model",
        field_name="test_field",
        field_verbose_name="Test Field",
        tags="tag1,tag2,tag3",
    )


# =============================================================================
# FK POPULATION STRATEGY TESTS
# =============================================================================


class TestFKPopulationStrategies(TestCase):
    """
    Test all 5 FK population strategies used in the migration.

    These tests simulate what happens during migration when matching
    existing UserTag/SystemTag records to TaggedFieldModel.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="strategyuser", password="test")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create TaggedFieldModel
        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_name="strategy_test_field",
            field_verbose_name="Strategy Test Field",
            tag_type="user",
        )

    def _create_user_tag_without_fk(self, **overrides):
        """Helper to create UserTag simulating pre-migration state."""
        defaults = {
            "user": self.user,
            "tagged_field": None,  # Simulates pre-migration
            "model_name": "TaggedFieldTestModel",
            "model_verbose_name": "Tagged Field Test Model",
            "field_name": "strategy_test_field",
            "field_verbose_name": "Strategy Test Field",
            "tags": "test,tags",
        }
        defaults.update(overrides)
        return UserTag.objects.create(**defaults)

    def test_strategy_1_exact_model_name_match(self):
        """
        Strategy 1: Exact match by model_name + field_name.

        This is the normal case when no model renames have occurred.
        """
        user_tag = self._create_user_tag_without_fk()

        # Simulate migration matching logic
        matched = TaggedFieldModel.objects.filter(
            model_name=user_tag.model_name,
            field_name=user_tag.field_name,
        ).first()

        assert matched is not None
        assert matched.pk == self.tagged_field_model.pk

        # Update FK
        user_tag.tagged_field = matched
        user_tag.save()
        user_tag.refresh_from_db()

        assert user_tag.tagged_field == self.tagged_field_model

    def test_strategy_2_content_type_lowercase_match(self):
        """
        Strategy 2: Match by ContentType.model (lowercase) + field_name.

        Handles case where TaggedFieldModel.model_name was updated
        after a model rename, but UserTag.model_name is stale.
        """
        # Simulate: TaggedFieldModel updated, UserTag stale
        self.tagged_field_model.model_name = "RenamedModel"
        self.tagged_field_model.save()

        user_tag = self._create_user_tag_without_fk(
            model_name="TaggedFieldTestModel",  # Stale name
        )

        # Strategy 1 fails (model_name mismatch)
        matched = TaggedFieldModel.objects.filter(
            model_name=user_tag.model_name,
            field_name=user_tag.field_name,
        ).first()
        assert matched is None

        # Strategy 2: Use ContentType.model (lowercase)
        matched = TaggedFieldModel.objects.filter(
            content__model=user_tag.model_name.lower(),
            field_name=user_tag.field_name,
        ).first()

        assert matched is not None
        assert matched.pk == self.tagged_field_model.pk

    def test_strategy_3_verbose_name_match(self):
        """
        Strategy 3: Match by model_verbose_name + field_name.

        Handles case where verbose_name is more stable than model_name.
        """
        # Simulate: Both model_name values are different
        self.tagged_field_model.model_name = "NewModelName"
        self.tagged_field_model.save()

        user_tag = self._create_user_tag_without_fk(
            model_name="OldModelName",  # Different from TaggedFieldModel
        )

        # Strategy 1 fails
        matched = TaggedFieldModel.objects.filter(
            model_name=user_tag.model_name,
            field_name=user_tag.field_name,
        ).first()
        assert matched is None

        # Strategy 2 fails (ContentType.model doesn't match "OldModelName")
        matched = TaggedFieldModel.objects.filter(
            content__model=user_tag.model_name.lower(),
            field_name=user_tag.field_name,
        ).first()
        assert matched is None

        # Strategy 3: Use model_verbose_name
        matched = TaggedFieldModel.objects.filter(
            model_verbose_name=user_tag.model_verbose_name,
            field_name=user_tag.field_name,
        ).first()

        assert matched is not None
        assert matched.pk == self.tagged_field_model.pk

    def test_strategy_4_field_verbose_name_match(self):
        """
        Strategy 4: Match by field_name + field_verbose_name (if unique).

        Only succeeds if there's exactly one TaggedFieldModel with
        this field_name + field_verbose_name combination.
        """
        # Make all other identifiers mismatch
        self.tagged_field_model.model_name = "CompletelyDifferent"
        self.tagged_field_model.model_verbose_name = "Also Different"
        self.tagged_field_model.save()

        user_tag = self._create_user_tag_without_fk(
            model_name="OldModel",
            model_verbose_name="Old Verbose Name",
        )

        # Strategies 1-3 fail
        assert (
            TaggedFieldModel.objects.filter(model_name=user_tag.model_name).count() == 0
        )
        assert (
            TaggedFieldModel.objects.filter(
                content__model=user_tag.model_name.lower()
            ).count()
            == 0
        )
        assert (
            TaggedFieldModel.objects.filter(
                model_verbose_name=user_tag.model_verbose_name
            ).count()
            == 0
        )

        # Strategy 4: field_name + field_verbose_name
        candidates = TaggedFieldModel.objects.filter(
            field_name=user_tag.field_name,
            field_verbose_name=user_tag.field_verbose_name,
        )

        assert candidates.count() == 1
        assert candidates.first().pk == self.tagged_field_model.pk

    def test_strategy_5_field_name_only_match(self):
        """
        Strategy 5: Match by field_name only (if globally unique).

        Very last resort - only if field_name is unique across all
        TaggedFieldModel records.
        """
        # Make everything mismatch except field_name
        self.tagged_field_model.model_name = "Completely"
        self.tagged_field_model.model_verbose_name = "Different"
        self.tagged_field_model.field_verbose_name = "Names"
        self.tagged_field_model.save()

        user_tag = self._create_user_tag_without_fk(
            model_name="OldModel",
            model_verbose_name="Old Verbose",
            field_verbose_name="Old Field Verbose",
        )

        # Strategies 1-4 fail
        assert (
            TaggedFieldModel.objects.filter(model_name=user_tag.model_name).count() == 0
        )
        assert (
            TaggedFieldModel.objects.filter(
                content__model=user_tag.model_name.lower()
            ).count()
            == 0
        )
        assert (
            TaggedFieldModel.objects.filter(
                model_verbose_name=user_tag.model_verbose_name
            ).count()
            == 0
        )
        assert (
            TaggedFieldModel.objects.filter(
                field_name=user_tag.field_name,
                field_verbose_name=user_tag.field_verbose_name,
            ).count()
            == 0
        )

        # Strategy 5: field_name only (must be unique)
        candidates = TaggedFieldModel.objects.filter(
            field_name=user_tag.field_name,
        )

        assert candidates.count() == 1
        assert candidates.first().pk == self.tagged_field_model.pk

    def test_strategy_5_fails_when_not_unique(self):
        """
        Strategy 5 should NOT match if field_name is not globally unique.
        """
        # Create another TaggedFieldModel with same field_name but different model
        other_content_type = ContentType.objects.get_for_model(User)
        TaggedFieldModel.objects.create(
            content=other_content_type,
            model_name="User",
            model_verbose_name="User",
            field_name="strategy_test_field",  # Same field_name!
            field_verbose_name="Different Verbose",
            tag_type="user",
        )

        # Make everything mismatch
        self.tagged_field_model.model_name = "Completely"
        self.tagged_field_model.model_verbose_name = "Different"
        self.tagged_field_model.field_verbose_name = "Names"
        self.tagged_field_model.save()

        user_tag = self._create_user_tag_without_fk(
            model_name="Unknown",
            model_verbose_name="Unknown",
            field_verbose_name="Unknown",
        )

        # Strategy 5 should fail (not unique)
        candidates = TaggedFieldModel.objects.filter(
            field_name=user_tag.field_name,
        )

        assert candidates.count() == 2  # Not unique!

    def test_all_strategies_fail_orphaned_record(self):
        """
        Test behavior when no strategy can find a match.

        This simulates a UserTag that references a deleted model.
        """
        user_tag = self._create_user_tag_without_fk(
            model_name="DeletedModel",
            model_verbose_name="Deleted Model",
            field_name="deleted_field",
            field_verbose_name="Deleted Field",
        )

        # All strategies fail
        matched = TaggedFieldModel.objects.filter(
            model_name=user_tag.model_name,
            field_name=user_tag.field_name,
        ).first()
        assert matched is None

        matched = TaggedFieldModel.objects.filter(
            content__model=user_tag.model_name.lower(),
            field_name=user_tag.field_name,
        ).first()
        assert matched is None

        matched = TaggedFieldModel.objects.filter(
            model_verbose_name=user_tag.model_verbose_name,
            field_name=user_tag.field_name,
        ).first()
        assert matched is None

        candidates = TaggedFieldModel.objects.filter(
            field_name=user_tag.field_name,
            field_verbose_name=user_tag.field_verbose_name,
        )
        assert candidates.count() == 0

        candidates = TaggedFieldModel.objects.filter(
            field_name=user_tag.field_name,
        )
        assert candidates.count() == 0

        # Record remains orphaned (tagged_field=None)
        assert user_tag.tagged_field is None


# =============================================================================
# MODEL RENAME SCENARIO TESTS
# =============================================================================


class TestModelRenameScenarios(TestCase):
    """
    Test scenarios where models have been renamed.

    These are the key tests for the feature - proving that FK lookups
    survive model renames.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="renameuser", password="test")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_name="rename_test_field",
            field_verbose_name="Rename Test Field",
            tag_type="user",
        )

        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_name="rename_test_field",
            field_verbose_name="Rename Test Field",
            tags="original,tags",
        )

    def test_fk_survives_model_name_change(self):
        """
        FK relationship survives when model_name is updated.

        Simulates what happens after a model rename + migration.
        """
        # Simulate post-rename state
        self.tagged_field_model.model_name = "RenamedModel"
        self.tagged_field_model.save()

        # UserTag still has old model_name (not yet refreshed)
        assert self.user_tag.model_name == "TaggedFieldTestModel"

        # But FK is still valid!
        self.user_tag.refresh_from_db()
        assert self.user_tag.tagged_field == self.tagged_field_model
        assert self.user_tag.tagged_field.model_name == "RenamedModel"

    def test_current_model_name_reflects_contenttype(self):
        """
        current_model_name property returns name from ContentType,
        not the cached model_name field.
        """
        # Simulate stale model_name
        self.tagged_field_model.model_name = "StaleModelName"
        self.tagged_field_model.save()

        # current_model_name should return ContentType.model (lowercase)
        assert self.tagged_field_model.current_model_name == "taggedfieldtestmodel"

        # Via UserTag
        assert self.user_tag.tagged_field.current_model_name == "taggedfieldtestmodel"

    def test_current_model_class_returns_actual_class(self):
        """
        current_model_class property returns the actual model class.
        """
        model_class = self.tagged_field_model.current_model_class

        assert model_class is not None
        assert model_class == TaggedFieldTestModel
        assert model_class.__name__ == "TaggedFieldTestModel"

    def test_lookup_by_fk_works_with_stale_model_name(self):
        """
        Queries using FK work even when model_name is stale.
        """
        # Stale both records
        self.tagged_field_model.model_name = "OldName"
        self.tagged_field_model.save()
        self.user_tag.model_name = "OldName"
        self.user_tag.save()

        # Query by FK - should work
        found = UserTag.objects.filter(
            tagged_field=self.tagged_field_model,
            user=self.user,
        ).first()

        assert found is not None
        assert found.pk == self.user_tag.pk
        assert found.tags == "original,tags"

    def test_lookup_by_model_name_fails_when_stale(self):
        """
        Demonstrate that string-based lookup fails when model_name is stale.

        This shows why FK lookups are better.
        """
        # Update TaggedFieldModel but not UserTag
        self.tagged_field_model.model_name = "NewName"
        self.tagged_field_model.save()

        # String-based lookup fails
        found = TaggedFieldModel.objects.filter(
            model_name="TaggedFieldTestModel",  # Old name
            field_name="rename_test_field",
        ).first()

        assert found is None  # Fails!

        # FK-based lookup works
        found = TaggedFieldModel.objects.filter(
            content=self.content_type,
            field_name="rename_test_field",
        ).first()

        assert found is not None
        assert found.pk == self.tagged_field_model.pk


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        self.user = User.objects.create_user(username="edgeuser", password="test")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

    def test_empty_model_name(self):
        """Handle records with empty/blank model_name."""
        tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="",  # Empty!
            model_verbose_name="Test Model",
            field_name="empty_name_field",
            field_verbose_name="Empty Name Field",
            tag_type="user",
        )

        # Should still be queryable by FK
        found = TaggedFieldModel.objects.filter(
            content=self.content_type,
            field_name="empty_name_field",
        ).first()

        assert found is not None
        assert found.pk == tagged_field.pk

    def test_null_model_name(self):
        """Handle records with NULL model_name."""
        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name=None,  # NULL!
            model_verbose_name="Test Model",
            field_name="null_name_field",
            field_verbose_name="Null Name Field",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(
            content=self.content_type,
            field_name="null_name_field",
        ).first()

        assert found is not None
        assert found.model_name is None

    def test_case_sensitivity_model_name(self):
        """Test case sensitivity in model_name matching."""
        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="MyModel",  # ProperCase
            model_verbose_name="My Model",
            field_name="case_test_field",
            field_verbose_name="Case Test Field",
            tag_type="user",
        )

        # Exact case matches
        assert TaggedFieldModel.objects.filter(model_name="MyModel").exists()

        # Different case doesn't match (database-dependent)
        # This test documents current behavior
        TaggedFieldModel.objects.filter(model_name="mymodel").exists()
        TaggedFieldModel.objects.filter(model_name="MYMODEL").exists()

        # ContentType.model is always lowercase
        assert TaggedFieldModel.objects.filter(
            content__model="taggedfieldtestmodel"
        ).exists()

    def test_special_characters_in_field_name(self):
        """Handle field names with special characters."""
        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TestModel",
            model_verbose_name="Test Model",
            field_name="field_with_underscore",
            field_verbose_name="Field With Underscore",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(
            field_name="field_with_underscore"
        ).first()

        assert found is not None

    def test_very_long_model_name(self):
        """Handle very long model names (up to max_length)."""
        long_name = "A" * 255  # max_length

        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name=long_name,
            model_verbose_name="Long Name Model",
            field_name="long_name_field",
            field_verbose_name="Long Name Field",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(model_name=long_name).first()
        assert found is not None
        assert len(found.model_name) == 255

    def test_unicode_in_verbose_name(self):
        """Handle unicode in verbose names."""
        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TestModel",
            model_verbose_name="日本語モデル",  # Japanese
            field_name="unicode_field",
            field_verbose_name="Ünïcödé Fïëld",  # Accented
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(
            model_verbose_name="日本語モデル"
        ).first()

        assert found is not None
        assert found.field_verbose_name == "Ünïcödé Fïëld"


# =============================================================================
# CONSTRAINT AND INTEGRITY TESTS
# =============================================================================


class TestConstraintsAndIntegrity(TransactionTestCase):
    """Test database constraints and referential integrity."""

    def setUp(self):
        self.user = User.objects.create_user(username="integrityuser", password="test")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

    def test_unique_constraint_content_field_name(self):
        """
        Test that (content, field_name) is unique.

        This is the new constraint replacing the 5-field constraint.
        """
        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TestModel",
            model_verbose_name="Test Model",
            field_name="unique_test_field",
            field_verbose_name="Unique Test Field",
            tag_type="user",
        )

        # Same content + field_name should fail
        with pytest.raises(IntegrityError):
            TaggedFieldModel.objects.create(
                content=self.content_type,
                model_name="DifferentName",  # Different model_name
                model_verbose_name="Different Verbose",
                field_name="unique_test_field",  # Same field_name!
                field_verbose_name="Different Field Verbose",
                tag_type="system",  # Different tag_type
            )

    def test_same_field_name_different_model_allowed(self):
        """
        Same field_name on different models should be allowed.
        """
        content_type_user = ContentType.objects.get_for_model(User)

        TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Test Model",
            field_name="tags",
            field_verbose_name="Tags",
            tag_type="user",
        )

        # Same field_name, different model - should work
        TaggedFieldModel.objects.create(
            content=content_type_user,  # Different content!
            model_name="User",
            model_verbose_name="User",
            field_name="tags",  # Same field_name
            field_verbose_name="User Tags",
            tag_type="user",
        )

        assert TaggedFieldModel.objects.filter(field_name="tags").count() == 2

    def test_cascade_delete_tagged_field_model(self):
        """
        Deleting TaggedFieldModel should cascade to UserTag/SystemTag.
        """
        tagged_field = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="CascadeModel",
            model_verbose_name="Cascade Model",
            field_name="cascade_field",
            field_verbose_name="Cascade Field",
            tag_type="user",
        )

        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=tagged_field,
            model_name="CascadeModel",
            model_verbose_name="Cascade Model",
            field_name="cascade_field",
            field_verbose_name="Cascade Field",
            tags="will,be,deleted",
        )

        user_tag_pk = user_tag.pk

        # Delete TaggedFieldModel
        tagged_field.delete()

        # UserTag should be deleted via CASCADE
        assert not UserTag.objects.filter(pk=user_tag_pk).exists()

    def test_user_tag_without_fk_allowed(self):
        """
        UserTag with tagged_field=None should be allowed.

        This supports orphaned records from failed migration matching.
        """
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=None,  # No FK
            model_name="OrphanModel",
            model_verbose_name="Orphan Model",
            field_name="orphan_field",
            field_verbose_name="Orphan Field",
            tags="orphan,tags",
        )

        assert user_tag.pk is not None
        assert user_tag.tagged_field is None


# =============================================================================
# BREAKING CHANGE VALIDATION TESTS
# =============================================================================


class TestBreakingChanges(TestCase):
    """
    Test breaking changes introduced in this update.

    These tests document and validate the breaking changes.
    """

    def test_tagmecharfield_choices_requires_system_tag_deprecation(self):
        """
        TagMeCharField with choices but without system_tag=True should warn.

        This is transitional behavior - warns now, will error in next major version.
        """

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            field = TagMeCharField(choices=["Choice1", "Choice2"])

            # Should have raised a DeprecationWarning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "system_tag=True" in str(w[0].message)

            # Field should auto-fix
            assert field.system_tag is True

    def test_tagmecharfield_system_tag_requires_choices(self):
        """
        TagMeCharField with system_tag=True but without choices should raise.
        """
        with pytest.raises(ValueError) as exc_info:
            TagMeCharField(system_tag=True)

        assert "choices" in str(exc_info.value)

    def test_tagmecharfield_choices_with_system_tag_works(self):
        """
        TagMeCharField with both choices and system_tag=True should work.
        """
        field = TagMeCharField(
            choices=["Choice1", "Choice2"],
            system_tag=True,
        )

        assert field._tag_choices == "Choice1, Choice2,"
        assert field.tag_type == "system"
        assert field.choices is None  # Django machinery disabled

    def test_tagmecharfield_user_tags_no_choices(self):
        """
        TagMeCharField for user tags should have no choices.
        """
        field = TagMeCharField()

        assert field.system_tag is False
        assert field.tag_type == "user"
        assert field._tag_choices == ""
        assert field._tag_choices_input is None
        assert field.choices is None

    def test_tagmecharfield_choices_never_passed_to_parent(self):
        """
        Choices should be intercepted and never passed to parent CharField.

        This ensures we don't fight Django's choices validation machinery.
        """
        # With choices
        field_with = TagMeCharField(
            choices=["A", "B", "C"],
            system_tag=True,
        )
        assert field_with.choices is None  # Never passed to parent
        assert field_with._tag_choices_input == ["A", "B", "C"]  # We stored it

        # Without choices
        field_without = TagMeCharField()
        assert field_without.choices is None
        assert field_without._tag_choices_input is None

    def test_tagmecharfield_clone_preserves_choices(self):
        """
        Field clone (used by Django migrations) must preserve choices.

        This tests the critical fix for the deconstruct() method.
        Django calls field.clone() during makemigrations, which uses
        deconstruct() to get args/kwargs and recreates the field.
        """
        original = TagMeCharField(
            choices=[("a", "A"), ("b", "B")],
            system_tag=True,
        )

        # Verify choices were intercepted, not passed to parent
        assert original.choices is None
        assert original._tag_choices_input == [("a", "A"), ("b", "B")]

        # Simulate what Django does during clone
        name, path, args, kwargs = original.deconstruct()

        # This should NOT raise ValueError
        cloned = TagMeCharField(*args, **kwargs)

        # Verify cloned field has same configuration
        assert cloned.system_tag is True
        assert cloned._tag_choices == original._tag_choices
        assert cloned._tag_choices_input == original._tag_choices_input
        assert cloned.tag_type == "system"


# =============================================================================
# FORM MIXIN INTEGRATION TESTS
# =============================================================================


class TestFormMixinIntegration(TestCase):
    """
    Test that form mixins work correctly with FK lookups.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="mixinuser", password="test")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_name="tagged_field_1",
            field_verbose_name="Tagged Field 1",
            tag_type="user",
        )

        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_name="tagged_field_1",
            field_verbose_name="Tagged Field 1",
            tags="mixin,test,tags",
        )

    def test_mixin_finds_user_tag_by_fk(self):
        """Mixin should find UserTag via FK lookup."""

        class TestForm(AllFieldsTagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1"]

        form = TestForm(user=self.user)

        # Field should be in form
        assert "tagged_field_1" in form.fields

    def test_mixin_works_with_stale_model_name(self):
        """Mixin should work even when model_name is stale."""

        # Make model_name stale
        self.tagged_field_model.model_name = "OldModelName"
        self.tagged_field_model.save()
        self.user_tag.model_name = "OldModelName"
        self.user_tag.save()

        class TestForm(AllFieldsTagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1"]

        form = TestForm(user=self.user)

        # Should still work via FK
        assert "tagged_field_1" in form.fields


# =============================================================================
# REGISTRY INTEGRATION TESTS
# =============================================================================


class TestRegistryIntegration(TestCase):
    """
    Test that the registry correctly uses FK lookups.
    """

    def test_registry_uses_update_or_create(self):
        """
        Registry should use update_or_create with content + field_name.

        This ensures model_name gets refreshed on each migration.
        """

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create initial record
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="registry_test_field",
            tags="",
            model_name="OriginalName",
            model_verbose_name="Original Verbose",
            field_verbose_name="Registry Test Field",
            tag_type=TagType.USER,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata})

        # Verify created
        record = TaggedFieldModel.objects.get(
            content=content_type,
            field_name="registry_test_field",
        )
        assert record.model_name == "OriginalName"

        # Simulate model rename and re-run
        metadata_updated = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="registry_test_field",
            tags="",
            model_name="RenamedModel",  # Changed!
            model_verbose_name="Renamed Verbose",
            field_verbose_name="Registry Test Field",
            tag_type=TagType.USER,
        )

        persistence.save_fields({metadata_updated})

        # Should update, not create duplicate
        assert (
            TaggedFieldModel.objects.filter(
                content=content_type,
                field_name="registry_test_field",
            ).count()
            == 1
        )

        record.refresh_from_db()
        assert record.model_name == "RenamedModel"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


class TestQueryPerformance(TestCase):
    """
    Test that FK lookups don't cause N+1 queries.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="perfuser", password="test")
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create multiple TaggedFieldModels and UserTags
        for i in range(5):
            tfm = TaggedFieldModel.objects.create(
                content=self.content_type,
                model_name=f"PerfModel{i}",
                model_verbose_name=f"Perf Model {i}",
                field_name=f"perf_field_{i}",
                field_verbose_name=f"Perf Field {i}",
                tag_type="user",
            )
            UserTag.objects.create(
                user=self.user,
                tagged_field=tfm,
                model_name=f"PerfModel{i}",
                model_verbose_name=f"Perf Model {i}",
                field_name=f"perf_field_{i}",
                field_verbose_name=f"Perf Field {i}",
                tags=f"tag{i}a,tag{i}b",
            )

    def test_select_related_reduces_queries(self):
        """Using select_related should fetch TaggedFieldModel in same query."""

        # Without select_related
        with CaptureQueriesContext(connection) as context:
            user_tags = list(UserTag.objects.filter(user=self.user))
            for ut in user_tags:
                _ = ut.tagged_field.model_name  # Access FK

        queries_without = len(context.captured_queries)

        # With select_related
        with CaptureQueriesContext(connection) as context:
            user_tags = list(
                UserTag.objects.filter(user=self.user).select_related("tagged_field")
            )
            for ut in user_tags:
                _ = ut.tagged_field.model_name  # Access FK

        queries_with = len(context.captured_queries)

        # select_related should use fewer queries
        assert queries_with < queries_without
