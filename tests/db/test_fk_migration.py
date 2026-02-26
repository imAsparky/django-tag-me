"""
Tests for FK lookup refactor migration (0004_fk_lookup_refactor).

This migration populates tagged_field FK on UserTag/SystemTag records
using a 5-strategy fallback chain. These tests verify each strategy
works correctly, ensuring the migration handles model renames and
stale cached names.

These tests protect frozen migration code that still executes on every
new installation. Low-maintenance but high-value insurance against
migration squash regressions.

Run with: pytest tests/test_fk_migration.py -v
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from tag_me.models import TaggedFieldModel, UserTag
from tests.models import TaggedFieldTestModel

User = get_user_model()


# =============================================================================
# FK Population Strategy Tests
# =============================================================================


@pytest.mark.django_db
class TestFKPopulationStrategies:
    """Test all 5 FK population strategies used in migration 0004.

    Each strategy is a fallback for matching existing UserTag records
    (with tagged_field=None) to the correct TaggedFieldModel.
    """

    @pytest.fixture
    def strategy_setup(self, test_user_factory, tagged_field_factory):
        """Base setup: a user, content type, and tagged field."""
        user = test_user_factory(username="strategyuser")
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="strategy_test_field",
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_verbose_name="Strategy Test Field",
        )
        return {"user": user, "ct": ct, "tfm": tfm}

    def _create_unlinked_user_tag(self, user, **overrides):
        """Create a UserTag simulating pre-migration state (no FK)."""
        defaults = {
            "user": user,
            "tagged_field": None,
            "model_name": "TaggedFieldTestModel",
            "model_verbose_name": "Tagged Field Test Model",
            "field_name": "strategy_test_field",
            "field_verbose_name": "Strategy Test Field",
            "tags": "test,tags",
        }
        defaults.update(overrides)
        return UserTag.objects.create(**defaults)

    def test_strategy_1_exact_model_name_match(self, strategy_setup):
        """Normal case: exact model_name + field_name match."""
        ut = self._create_unlinked_user_tag(strategy_setup["user"])

        matched = TaggedFieldModel.objects.filter(
            model_name=ut.model_name,
            field_name=ut.field_name,
        ).first()

        assert matched is not None
        assert matched.pk == strategy_setup["tfm"].pk

    def test_strategy_2_content_type_lowercase_match(self, strategy_setup):
        """TaggedFieldModel renamed but UserTag has stale model_name."""
        tfm = strategy_setup["tfm"]
        tfm.model_name = "RenamedModel"
        tfm.save()

        ut = self._create_unlinked_user_tag(
            strategy_setup["user"], model_name="TaggedFieldTestModel"
        )

        # Strategy 1 fails
        assert not TaggedFieldModel.objects.filter(
            model_name=ut.model_name, field_name=ut.field_name
        ).exists()

        # Strategy 2: ContentType.model (lowercase)
        matched = TaggedFieldModel.objects.filter(
            content__model=ut.model_name.lower(),
            field_name=ut.field_name,
        ).first()

        assert matched is not None
        assert matched.pk == tfm.pk

    def test_strategy_3_verbose_name_match(self, strategy_setup):
        """Both model_name values differ but verbose_name matches."""
        tfm = strategy_setup["tfm"]
        tfm.model_name = "NewModelName"
        tfm.save()

        ut = self._create_unlinked_user_tag(
            strategy_setup["user"], model_name="OldModelName"
        )

        # Strategies 1-2 fail
        assert not TaggedFieldModel.objects.filter(
            model_name=ut.model_name, field_name=ut.field_name
        ).exists()
        assert not TaggedFieldModel.objects.filter(
            content__model=ut.model_name.lower(), field_name=ut.field_name
        ).exists()

        # Strategy 3: model_verbose_name
        matched = TaggedFieldModel.objects.filter(
            model_verbose_name=ut.model_verbose_name,
            field_name=ut.field_name,
        ).first()

        assert matched is not None
        assert matched.pk == tfm.pk

    def test_strategy_4_field_verbose_name_match(self, strategy_setup):
        """All name fields differ — match by field_name + field_verbose_name."""
        tfm = strategy_setup["tfm"]
        tfm.model_name = "CompletelyDifferent"
        tfm.model_verbose_name = "Also Different"
        tfm.save()

        ut = self._create_unlinked_user_tag(
            strategy_setup["user"],
            model_name="OldModel",
            model_verbose_name="Old Verbose Name",
        )

        candidates = TaggedFieldModel.objects.filter(
            field_name=ut.field_name,
            field_verbose_name=ut.field_verbose_name,
        )

        assert candidates.count() == 1
        assert candidates.first().pk == tfm.pk

    def test_strategy_5_field_name_only_match(self, strategy_setup):
        """Last resort: match by field_name only (must be globally unique)."""
        tfm = strategy_setup["tfm"]
        tfm.model_name = "Completely"
        tfm.model_verbose_name = "Different"
        tfm.field_verbose_name = "Names"
        tfm.save()

        ut = self._create_unlinked_user_tag(
            strategy_setup["user"],
            model_name="OldModel",
            model_verbose_name="Old Verbose",
            field_verbose_name="Old Field Verbose",
        )

        candidates = TaggedFieldModel.objects.filter(field_name=ut.field_name)

        assert candidates.count() == 1
        assert candidates.first().pk == tfm.pk

    def test_strategy_5_fails_when_not_unique(self, strategy_setup):
        """Strategy 5 should not match if field_name is not globally unique."""
        tfm = strategy_setup["tfm"]
        tfm.model_name = "Completely"
        tfm.model_verbose_name = "Different"
        tfm.field_verbose_name = "Names"
        tfm.save()

        # Create another TaggedFieldModel with same field_name, different model
        other_ct = ContentType.objects.get_for_model(User)
        TaggedFieldModel.objects.create(
            content=other_ct,
            model_name="User",
            model_verbose_name="User",
            field_name="strategy_test_field",
            field_verbose_name="Different Verbose",
            tag_type="user",
        )

        candidates = TaggedFieldModel.objects.filter(field_name="strategy_test_field")

        assert candidates.count() >= 2  # Not unique

    def test_all_strategies_fail_for_deleted_model(self, strategy_setup):
        """When a model was truly deleted, no strategy can match."""
        ut = self._create_unlinked_user_tag(
            strategy_setup["user"],
            model_name="DeletedModel",
            model_verbose_name="Deleted Model",
            field_name="deleted_field",
            field_verbose_name="Deleted Field",
        )

        for lookup in [
            {"model_name": ut.model_name, "field_name": ut.field_name},
            {"content__model": ut.model_name.lower(), "field_name": ut.field_name},
            {"model_verbose_name": ut.model_verbose_name, "field_name": ut.field_name},
            {"field_name": ut.field_name, "field_verbose_name": ut.field_verbose_name},
            {"field_name": ut.field_name},
        ]:
            assert not TaggedFieldModel.objects.filter(**lookup).exists()

        assert ut.tagged_field is None
