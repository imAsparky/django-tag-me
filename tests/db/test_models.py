"""
Tests for tag-me models.

Covers:
    - TagBase: properties, slug generation, collision retry
    - TaggedFieldModel: validation, __str__, properties, edge cases
    - TagMeSynchronise: sync list methods, check_field_sync_list_lengths
    - UserTag: NULL handling, __str__, save synchronization
    - SystemTag: NULL handling, __str__, unique constraint
    - FK resilience: lookups survive model renames
    - Cascade: TaggedFieldModel delete cascades to UserTag/SystemTag
    - Performance: select_related reduces queries
    - current_model_name property: TFM, UserTag, SystemTag (live vs cached)
    - Model schema: help_text on model_name fields

Tests absorbed from test_deep_review_fixes.py:
    - TestNullHandling
    - TestTaggedFieldModelValidation
    - TestTagMeSynchronise (sync list methods)
    - TestSlugCollisionRetry
    - TestSystemTagConstraint

Tests absorbed from test_fk_migration.py:
    - TestModelRenameScenarios (FK resilience)
    - TestEdgeCases (boundary conditions)
    - TestConstraintsAndIntegrity (cascade delete)
    - TestQueryPerformance

Tests absorbed from test_model_properties.py:
    - TestCurrentModelNameProperty (TFM, UserTag, SystemTag)
    - TestModelNameFieldHelpText
"""

import logging
import string
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from hypothesis import given
from hypothesis import strategies as st

from tag_me.models import (
    SystemTag,
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tests.models import TaggedFieldTestModel

User = get_user_model()

logger = logging.getLogger(__name__)

# Valid tag types — must match models.py
TAG_TYPES = ["user", "system"]
TAG_TYPE_DEFAULT = "user"


# =============================================================================
# TagBase Properties & Slug
# =============================================================================


@pytest.mark.django_db
class TestTagBaseProperties:
    """Test TagBase model properties and class-level attributes."""

    def test_model_class_verbose_name(self):
        model = TaggedFieldTestModel()
        assert model.model_class_verbose_name == "Tagged Field Test Model"

    def test_model_class_name(self):
        model = TaggedFieldTestModel()
        assert model.model_class_name == "TaggedFieldTestModel"


@pytest.mark.django_db
class TestTagBaseSlug:
    """Test slug generation and collision retry logic."""

    def test_slugify_contains_tag_text(self):
        tag = "asdf"
        assert tag in TaggedFieldTestModel.slugify(tag)

    @given(
        st_name=st.text(
            alphabet=string.ascii_letters,
            min_size=1,
            max_size=50,
        )
    )
    def test_slug_generated_with_sufficient_length(self, st_name):
        tag = TaggedFieldTestModel.objects.create(tags=st_name)
        assert len(tag.slug) >= 8

    def test_different_tags_get_different_slugs(self, test_user_factory):
        """Two tags with same content should still get unique slugs."""
        user1 = test_user_factory(username="slug_user1")
        user2 = test_user_factory(username="slug_user2")

        ct, _ = ContentType.objects.get_or_create(
            app_label="tests", model="slugtestmodel"
        )
        tfm = TaggedFieldModel.objects.create(
            content=ct,
            model_name="SlugTestModel",
            field_name="test_field",
            tag_type="user",
        )

        ut1 = UserTag.objects.create(
            user=user1,
            tagged_field=tfm,
            model_name="SlugTestModel",
            field_name="test_field",
            tags="same_tags,",
        )
        ut2 = UserTag.objects.create(
            user=user2,
            tagged_field=tfm,
            model_name="SlugTestModel",
            field_name="test_field2",
            tags="same_tags,",
        )

        assert ut1.slug != ut2.slug

    @pytest.mark.django_db(transaction=True)
    @patch("tag_me.models.TagBase.slugify")
    def test_slug_retry_exhaustion_raises(self, mock_slugify, test_user_factory):
        """After max retries with the same slug, IntegrityError should propagate.

        Uses transaction=True because IntegrityError breaks the current
        savepoint and we need real transaction rollback behavior.
        """
        mock_slugify.return_value = "always-same-slug"

        user1 = test_user_factory(username="retry_user1")
        user2 = test_user_factory(username="retry_user2")

        ct, _ = ContentType.objects.get_or_create(app_label="tests", model="retrymodel")
        tfm = TaggedFieldModel.objects.create(
            content=ct,
            model_name="RetryModel",
            field_name="test_field",
            tag_type="user",
        )

        # First tag claims the slug
        UserTag.objects.create(
            user=user1,
            tagged_field=tfm,
            model_name="RetryModel",
            field_name="test_field",
            tags="tag1,",
            slug="always-same-slug",
        )

        # Second tag can't get a different slug — should fail after retries
        ut2 = UserTag(
            user=user2,
            tagged_field=tfm,
            model_name="RetryModel",
            field_name="test_field2",
            tags="tag1,",
        )

        with pytest.raises(IntegrityError):
            ut2.save()


# =============================================================================
# TaggedFieldModel Validation & String Representation
# =============================================================================


@pytest.mark.django_db
class TestTaggedFieldModelValidation:
    """Test TaggedFieldModel.save() validation."""

    def test_save_requires_field_name(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tfm = TaggedFieldModel(
            content=ct,
            model_name="TestModel",
            field_name=None,
            tag_type="user",
        )

        with pytest.raises(ValueError, match="field_name cannot be empty"):
            tfm.save()

    def test_save_requires_content(self):
        tfm = TaggedFieldModel(
            content=None,
            model_name="TestModel",
            field_name="test_field",
            tag_type="user",
        )

        with pytest.raises(ValueError, match="content cannot be empty"):
            tfm.save()

    def test_save_validates_tag_type(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tfm = TaggedFieldModel(
            content=ct,
            model_name="TestModel",
            field_name="test_field",
            tag_type="invalid_type",
        )

        with pytest.raises(ValueError, match="tag_type must be one of"):
            tfm.save()

    def test_save_accepts_all_valid_tag_types(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        for tag_type in TAG_TYPES:
            tfm = TaggedFieldModel(
                content=ct,
                model_name="TestModel",
                field_name=f"field_{tag_type}",
                tag_type=tag_type,
            )
            tfm.save()
            assert tfm.pk is not None
            tfm.delete()

    def test_tag_type_default_is_valid(self):
        assert TAG_TYPE_DEFAULT in TAG_TYPES


@pytest.mark.django_db
class TestTaggedFieldModelStr:
    """Test TaggedFieldModel.__str__ with various NULL combinations."""

    def test_str_with_verbose_names(self, tagged_field_factory):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="test_field",
            model_verbose_name="My Model",
            field_verbose_name="My Field",
        )
        result = str(tfm)
        assert "My Model" in result
        assert "My Field" in result

    def test_str_with_null_verbose_names(self):
        """Should fall back to 'Unknown' when verbose names are NULL."""
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tfm = TaggedFieldModel.objects.create(
            content=ct,
            model_name=None,
            model_verbose_name=None,
            field_name="test_field",
            field_verbose_name=None,
            tag_type="user",
        )

        result = str(tfm)
        assert "Unknown" in result or "test_field" in result


# =============================================================================
# UserTag NULL Handling & String Representation
# =============================================================================


@pytest.mark.django_db
class TestUserTagNullHandling:
    """Test UserTag behavior with NULL fields."""

    def test_str_with_null_user(self, tagged_field_factory):
        """__str__ should show NO_USER when user is NULL."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="test_field",
        )
        user_tag = UserTag.objects.create(
            user=None,
            tagged_field=tfm,
            model_name="TestModel",
            field_name="test_field",
            tags="tag1,",
        )

        result = str(user_tag)
        assert "NO_USER" in result

    def test_save_with_null_tagged_field(self, test_user):
        """Should handle NULL tagged_field gracefully (orphaned record)."""
        user_tag = UserTag(
            user=test_user,
            tagged_field=None,
            model_name="DeletedModel",
            field_name="deleted_field",
            tags="tag1,",
        )

        user_tag.save()
        assert user_tag.pk is not None


# =============================================================================
# SystemTag NULL Handling & Constraint
# =============================================================================


@pytest.mark.django_db
class TestSystemTagNullHandling:
    """Test SystemTag behavior with NULL fields."""

    def test_str_with_null_verbose_names(self, tagged_field_factory):
        """__str__ should handle NULL verbose names gracefully."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="sys_field",
            tag_type="system",
        )
        system_tag = SystemTag.objects.create(
            tagged_field=tfm,
            model_name=None,
            model_verbose_name=None,
            field_name=None,
            tags="sys_tag,",
        )

        result = str(system_tag)
        assert "Unknown" in result


@pytest.mark.django_db
class TestSystemTagConstraint:
    """Test unique constraint: one SystemTag per TaggedFieldModel."""

    def test_duplicate_tagged_field_raises(self, tagged_field_factory):
        """Second SystemTag for the same TaggedFieldModel should fail."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="sys_field",
            tag_type="system",
        )

        SystemTag.objects.create(
            tagged_field=tfm,
            model_name="TestModel",
            field_name="sys_field",
            tags="sys1,",
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SystemTag.objects.create(
                    tagged_field=tfm,
                    model_name="TestModel",
                    field_name="sys_field",
                    tags="sys2,",
                )

    def test_null_tagged_field_allows_multiple(self):
        """Multiple SystemTags with NULL tagged_field are allowed (SQL NULL != NULL)."""
        st1 = SystemTag.objects.create(
            tagged_field=None,
            model_name="OrphanModel1",
            field_name="field1",
            tags="orphan1,",
        )
        st2 = SystemTag.objects.create(
            tagged_field=None,
            model_name="OrphanModel2",
            field_name="field2",
            tags="orphan2,",
        )

        assert st1.pk is not None
        assert st2.pk is not None


# =============================================================================
# TagMeSynchronise Methods
# =============================================================================


@pytest.mark.django_db
class TestTagMeSynchroniseMethods:
    """Test TagMeSynchronise helper methods."""

    def test_add_model_rejects_none_content_type(self):
        sync = TagMeSynchronise.objects.create(name="test_sync")
        assert sync._add_model_to_sync_list(content_type_id=None, field="f") is False

    def test_add_model_rejects_none_field(self):
        sync = TagMeSynchronise.objects.create(name="test_sync")
        assert sync._add_model_to_sync_list(content_type_id="123", field=None) is False

    def test_add_model_creates_field_list(self):
        sync = TagMeSynchronise.objects.create(name="test_sync", synchronise={})
        result = sync._add_model_to_sync_list(content_type_id="123", field="new_field")

        assert result is True
        assert "123" in sync.synchronise["new_field"]

    def test_add_model_prevents_duplicates(self):
        sync = TagMeSynchronise.objects.create(
            name="test_sync",
            synchronise={"test_field": ["123"]},
        )
        result = sync._add_model_to_sync_list(content_type_id="123", field="test_field")

        assert result is False
        assert sync.synchronise["test_field"].count("123") == 1

    def test_get_field_returns_list(self):
        sync = TagMeSynchronise.objects.create(
            name="test_sync",
            synchronise={"test_field": ["123", "456"]},
        )
        result = sync._get_field_name_models_to_sync("test_field")

        assert isinstance(result, list)
        assert result == ["123", "456"]

    def test_get_field_returns_none_for_missing(self):
        sync = TagMeSynchronise.objects.create(name="test_sync", synchronise={})
        assert sync._get_field_name_models_to_sync("nonexistent") is None


# =============================================================================
# TagMeSynchronise.check_field_sync_list_lengths
# =============================================================================


@pytest.mark.django_db
class TestCheckFieldSyncListLengths:
    """Test logging behavior for various sync list configurations."""

    def test_empty_dict_logs_info(self, caplog):
        sync = TagMeSynchronise.objects.create(name="test_empty", synchronise={})
        with caplog.at_level(logging.INFO):
            sync.check_field_sync_list_lengths()
        assert "no field tags listed that require synchronising" in caplog.text

    def test_zero_items_logs_warning(self, caplog):
        sync = TagMeSynchronise.objects.create(
            name="test_zero", synchronise={"empty_field": []}
        )
        with caplog.at_level(logging.WARNING):
            sync.check_field_sync_list_lengths()
        assert "empty_field" in caplog.text
        assert "no content id's listed" in caplog.text

    def test_one_item_logs_warning(self, caplog):
        sync = TagMeSynchronise.objects.create(
            name="test_one", synchronise={"lonely_field": [1]}
        )
        with caplog.at_level(logging.WARNING):
            sync.check_field_sync_list_lengths()
        assert "lonely_field" in caplog.text
        assert "only has 1 element" in caplog.text

    def test_two_items_logs_info(self, caplog):
        sync = TagMeSynchronise.objects.create(
            name="test_two", synchronise={"paired_field": [1, 2]}
        )
        with caplog.at_level(logging.INFO):
            sync.check_field_sync_list_lengths()
        assert "paired_field" in caplog.text
        assert "2 required minumum elements" in caplog.text

    def test_more_than_two_items_logs_info(self, caplog):
        sync = TagMeSynchronise.objects.create(
            name="test_many", synchronise={"multi_field": [1, 2, 3, 4]}
        )
        with caplog.at_level(logging.INFO):
            sync.check_field_sync_list_lengths()
        assert "multi_field" in caplog.text
        assert "more than the 2 required minumum elements" in caplog.text


# =============================================================================
# UserTag.save() Synchronization
# =============================================================================


@pytest.mark.django_db
class TestUserTagSaveSynchronization:
    """Test UserTag.save() tag synchronization logic.

    Uses fake ContentTypes to isolate from real registered fields.
    """

    @pytest.fixture
    def sync_setup(self, test_user_factory, tagged_field_factory):
        """Create a sync configuration with two related models.

        Returns dict with ct1, ct2, tf1, tf2, sync, user.
        """
        ct1, _ = ContentType.objects.get_or_create(
            app_label="tests", model="syncmodel1"
        )
        ct2, _ = ContentType.objects.get_or_create(
            app_label="tests", model="syncmodel2"
        )

        tf1 = tagged_field_factory(
            content_type=ct1,
            field_name="shared_tags",
            model_name="SyncModel1",
            model_verbose_name="Sync Model 1",
        )
        tf2 = tagged_field_factory(
            content_type=ct2,
            field_name="shared_tags",
            model_name="SyncModel2",
            model_verbose_name="Sync Model 2",
        )

        sync, _ = TagMeSynchronise.objects.get_or_create(name="default")
        sync.synchronise = {"shared_tags": [ct1.id, ct2.id]}
        sync.save()

        user = test_user_factory(username="syncuser")

        return {
            "ct1": ct1,
            "ct2": ct2,
            "tf1": tf1,
            "tf2": tf2,
            "sync": sync,
            "user": user,
        }

    def test_save_syncs_tags_to_related_usertag(self, sync_setup):
        """Saving should propagate tags to related UserTag."""
        user = sync_setup["user"]
        tf1, tf2 = sync_setup["tf1"], sync_setup["tf2"]

        ut1 = UserTag.objects.create(
            user=user,
            tagged_field=tf1,
            model_name="SyncModel1",
            field_name="shared_tags",
            tags="initial,",
        )
        ut2 = UserTag.objects.create(
            user=user,
            tagged_field=tf2,
            model_name="SyncModel2",
            field_name="shared_tags",
            tags="initial,",
        )

        ut1.tags = "synced,tags,"
        ut1.save()

        ut2.refresh_from_db()
        assert ut2.tags == "synced,tags,"

    def test_sync_tags_save_true_skips_sync(self, sync_setup):
        """sync_tags_save=True should skip synchronization (prevents loops)."""
        user = sync_setup["user"]
        tf1, tf2 = sync_setup["tf1"], sync_setup["tf2"]

        ut1 = UserTag.objects.create(
            user=user,
            tagged_field=tf1,
            model_name="SyncModel1",
            field_name="shared_tags",
            tags="original,",
        )
        ut2 = UserTag.objects.create(
            user=user,
            tagged_field=tf2,
            model_name="SyncModel2",
            field_name="shared_tags",
            tags="original,",
        )

        ut1.tags = "not_synced,"
        ut1.save(sync_tags_save=True)

        ut2.refresh_from_db()
        assert ut2.tags == "original,"

    def test_null_tagged_field_logs_warning(self, sync_setup, caplog):
        """UserTag without tagged_field should log and skip sync."""
        user = sync_setup["user"]

        ut = UserTag(
            user=user,
            tagged_field=None,
            model_name="OrphanModel",
            field_name="shared_tags",
            tags="orphan,",
        )

        with caplog.at_level(logging.WARNING):
            ut.save()

        assert "has no tagged_field FK" in caplog.text
        assert "skipping tag synchronization" in caplog.text

    def test_handles_missing_related_usertag(self, sync_setup, caplog):
        """Should log warning when related UserTag doesn't exist."""
        user = sync_setup["user"]
        tf1 = sync_setup["tf1"]
        # No UserTag for tf2

        ut1 = UserTag.objects.create(
            user=user,
            tagged_field=tf1,
            model_name="SyncModel1",
            field_name="shared_tags",
            tags="initial,",
        )

        with caplog.at_level(logging.WARNING):
            ut1.tags = "updated,"
            ut1.save()

        assert "Could not sync tags" in caplog.text

    def test_handles_missing_tagged_field_model(self, sync_setup, caplog):
        """Should log warning when TaggedFieldModel doesn't exist for content_id."""
        user = sync_setup["user"]
        tf1 = sync_setup["tf1"]
        sync = sync_setup["sync"]

        # Add a non-existent content_id to sync config
        sync.synchronise["shared_tags"].append(99999)
        sync.save()

        ut1 = UserTag.objects.create(
            user=user,
            tagged_field=tf1,
            model_name="SyncModel1",
            field_name="shared_tags",
            tags="initial,",
        )

        with caplog.at_level(logging.WARNING):
            ut1.tags = "updated,"
            ut1.save()

        assert "Could not sync tags" in caplog.text

    def test_field_not_in_sync_config_saves_normally(self, sync_setup):
        """Fields not in sync config should save without triggering sync."""
        user = sync_setup["user"]
        ct1 = sync_setup["ct1"]

        tf_private = TaggedFieldModel.objects.create(
            content=ct1,
            model_name="SyncModel1",
            field_name="private_tags",
            tag_type="user",
        )

        ut = UserTag.objects.create(
            user=user,
            tagged_field=tf_private,
            model_name="SyncModel1",
            field_name="private_tags",
            tags="private,",
        )

        ut.tags = "updated_private,"
        ut.save()

        ut.refresh_from_db()
        assert ut.tags == "updated_private,"


# =============================================================================
# FK Resilience (model rename scenarios)
# =============================================================================


@pytest.mark.django_db
class TestFKResilience:
    """Test that FK-based lookups survive model renames.

    Absorbed from test_fk_migration.py TestModelRenameScenarios.
    """

    @pytest.fixture
    def rename_setup(self, test_user_factory, tagged_field_factory):
        user = test_user_factory(username="renameuser")
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="rename_test_field",
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_verbose_name="Rename Test Field",
        )
        ut = UserTag.objects.create(
            user=user,
            tagged_field=tfm,
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_name="rename_test_field",
            field_verbose_name="Rename Test Field",
            tags="original,tags",
        )
        return {"user": user, "tfm": tfm, "ut": ut}

    def test_fk_survives_model_name_change(self, rename_setup):
        """FK relationship remains valid after model_name is updated."""
        tfm, ut = rename_setup["tfm"], rename_setup["ut"]

        tfm.model_name = "RenamedModel"
        tfm.save()

        # UserTag still has old model_name
        assert ut.model_name == "TaggedFieldTestModel"

        # But FK is still valid
        ut.refresh_from_db()
        assert ut.tagged_field == tfm
        assert ut.tagged_field.model_name == "RenamedModel"

    def test_fk_lookup_works_with_stale_model_name(self, rename_setup):
        """Querying by FK works even when cached names are stale."""
        tfm, ut, user = rename_setup["tfm"], rename_setup["ut"], rename_setup["user"]

        tfm.model_name = "OldName"
        tfm.save()
        ut.model_name = "OldName"
        ut.save(sync_tags_save=True)

        found = UserTag.objects.filter(
            tagged_field=tfm,
            user=user,
        ).first()

        assert found is not None
        assert found.pk == ut.pk
        assert found.tags == "original,tags"

    def test_string_lookup_fails_when_stale(self, rename_setup):
        """Demonstrates why FK lookups are better than string-based lookups."""
        tfm = rename_setup["tfm"]
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)

        tfm.model_name = "NewName"
        tfm.save()

        # String-based lookup fails
        assert not TaggedFieldModel.objects.filter(
            model_name="TaggedFieldTestModel",
            field_name="rename_test_field",
        ).exists()

        # FK-based lookup works
        found = TaggedFieldModel.objects.filter(
            content=ct,
            field_name="rename_test_field",
        ).first()

        assert found is not None
        assert found.pk == tfm.pk


# =============================================================================
# TaggedFieldModel Edge Cases
# =============================================================================


@pytest.mark.django_db
class TestTaggedFieldModelEdgeCases:
    """Test boundary conditions on TaggedFieldModel fields.

    Absorbed from test_fk_migration.py TestEdgeCases.
    """

    def test_empty_model_name_queryable_by_fk(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tfm = TaggedFieldModel.objects.create(
            content=ct,
            model_name="",
            model_verbose_name="Test Model",
            field_name="empty_name_field",
            field_verbose_name="Empty Name Field",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(
            content=ct, field_name="empty_name_field"
        ).first()

        assert found is not None
        assert found.pk == tfm.pk

    def test_null_model_name_queryable_by_fk(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        TaggedFieldModel.objects.create(
            content=ct,
            model_name=None,
            model_verbose_name="Test Model",
            field_name="null_name_field",
            field_verbose_name="Null Name Field",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(
            content=ct, field_name="null_name_field"
        ).first()

        assert found is not None
        assert found.model_name is None

    def test_case_sensitivity_of_model_name(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        TaggedFieldModel.objects.create(
            content=ct,
            model_name="MyModel",
            model_verbose_name="My Model",
            field_name="case_test_field",
            field_verbose_name="Case Test Field",
            tag_type="user",
        )

        # Exact case matches
        assert TaggedFieldModel.objects.filter(
            model_name="MyModel", field_name="case_test_field"
        ).exists()

        # ContentType.model is always lowercase
        assert TaggedFieldModel.objects.filter(
            content__model="taggedfieldtestmodel"
        ).exists()

    def test_underscore_in_field_name(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        TaggedFieldModel.objects.create(
            content=ct,
            model_name="TestModel",
            model_verbose_name="Test Model",
            field_name="field_with_underscore",
            field_verbose_name="Field With Underscore",
            tag_type="user",
        )

        assert TaggedFieldModel.objects.filter(
            field_name="field_with_underscore"
        ).exists()

    def test_max_length_model_name(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        long_name = "A" * 255

        TaggedFieldModel.objects.create(
            content=ct,
            model_name=long_name,
            model_verbose_name="Long Name Model",
            field_name="long_name_field",
            field_verbose_name="Long Name Field",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(model_name=long_name).first()
        assert found is not None
        assert len(found.model_name) == 255

    def test_unicode_in_verbose_names(self):
        ct = ContentType.objects.get_for_model(TaggedFieldTestModel)
        TaggedFieldModel.objects.create(
            content=ct,
            model_name="TestModel",
            model_verbose_name="\u65e5\u672c\u8a9e\u30e2\u30c7\u30eb",
            field_name="unicode_field",
            field_verbose_name="\u00dc\u006e\u00ef\u0063\u00f6\u0064\u00e9 F\u00ef\u00eb\u006c\u0064",
            tag_type="user",
        )

        found = TaggedFieldModel.objects.filter(
            model_verbose_name="\u65e5\u672c\u8a9e\u30e2\u30c7\u30eb"
        ).first()

        assert found is not None
        assert (
            found.field_verbose_name
            == "\u00dc\u006e\u00ef\u0063\u00f6\u0064\u00e9 F\u00ef\u00eb\u006c\u0064"
        )


# =============================================================================
# Cascade Delete
# =============================================================================


@pytest.mark.django_db
class TestCascadeDelete:
    """Test that deleting TaggedFieldModel cascades to related tags.

    Absorbed from test_fk_migration.py TestConstraintsAndIntegrity.
    """

    def test_deleting_tagged_field_cascades_to_user_tag(
        self, test_user, tagged_field_factory
    ):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="cascade_field",
            model_name="CascadeModel",
        )
        ut = UserTag.objects.create(
            user=test_user,
            tagged_field=tfm,
            model_name="CascadeModel",
            field_name="cascade_field",
            tags="will,be,deleted",
        )
        ut_pk = ut.pk

        tfm.delete()

        assert not UserTag.objects.filter(pk=ut_pk).exists()


# =============================================================================
# Query Performance
# =============================================================================


@pytest.mark.django_db
class TestQueryPerformance:
    """Test that select_related reduces N+1 queries.

    Absorbed from test_fk_migration.py TestQueryPerformance.
    """

    @pytest.fixture
    def perf_data(self, test_user, tagged_field_factory):
        """Create multiple TaggedFieldModels and UserTags for query testing."""
        tfms = []
        for i in range(5):
            tfm = tagged_field_factory(
                model_class=TaggedFieldTestModel,
                field_name=f"perf_field_{i}",
                model_name=f"PerfModel{i}",
            )
            UserTag.objects.create(
                user=test_user,
                tagged_field=tfm,
                model_name=f"PerfModel{i}",
                field_name=f"perf_field_{i}",
                tags=f"tag{i}a,tag{i}b",
            )
            tfms.append(tfm)
        return {"user": test_user, "tfms": tfms}

    def test_select_related_reduces_queries(self, perf_data):
        user = perf_data["user"]

        # Without select_related
        with CaptureQueriesContext(connection) as ctx_without:
            user_tags = list(UserTag.objects.filter(user=user))
            for ut in user_tags:
                _ = ut.tagged_field.model_name

        # With select_related
        with CaptureQueriesContext(connection) as ctx_with:
            user_tags = list(
                UserTag.objects.filter(user=user).select_related("tagged_field")
            )
            for ut in user_tags:
                _ = ut.tagged_field.model_name

        assert len(ctx_with.captured_queries) < len(ctx_without.captured_queries)


# =============================================================================
# current_model_name Property (absorbed from test_model_properties.py)
# =============================================================================


@pytest.mark.django_db
class TestCurrentModelNameProperty:
    """Test current_model_name on TaggedFieldModel, UserTag, and SystemTag.

    current_model_name reads from ContentType.model (always lowercase),
    bypassing the cached model_name field. This makes lookups resilient
    to model renames.

    Absorbed from test_model_properties.py.
    """

    # --- TaggedFieldModel ---

    def test_tfm_returns_live_value_not_cached(self, tagged_field_factory):
        """current_model_name returns ContentType.model, not stale model_name."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="prop_test_field",
            model_name="StaleModelName",
        )

        assert tfm.model_name == "StaleModelName"
        assert tfm.current_model_name == "taggedfieldtestmodel"

    def test_tfm_after_refresh_from_db(self, tagged_field_factory):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="refresh_test_field",
            model_name="StaleModelName",
        )
        tfm.refresh_from_db()

        assert tfm.current_model_name == "taggedfieldtestmodel"

    def test_tfm_current_model_class_is_usable(self, tagged_field_factory):
        """current_model_class should return a queryable model class."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="class_test_field",
            model_name="Anything",
        )
        model_class = tfm.current_model_class

        assert model_class is TaggedFieldTestModel
        assert isinstance(model_class.objects.count(), int)
        assert model_class.__name__ == "TaggedFieldTestModel"

    def test_tfm_properties_with_select_related(self, tagged_field_factory):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="prefetch_test_field",
        )

        fetched = TaggedFieldModel.objects.select_related("content").get(pk=tfm.pk)

        assert fetched.current_model_name == "taggedfieldtestmodel"
        assert fetched.current_model_class is TaggedFieldTestModel
        assert fetched.app_label == "tests"

    # --- UserTag ---

    def test_user_tag_returns_live_value(
        self, test_user, tagged_field_factory, user_tag_factory
    ):
        """UserTag.current_model_name should read via tagged_field FK chain."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="ut_prop_field",
            model_name="StaleModelName",
        )
        ut = user_tag_factory(
            user=test_user,
            tagged_field=tfm,
            model_name="StaleUserTagName",
            tags="tag1,tag2",
        )

        assert ut.model_name == "StaleUserTagName"
        assert ut.current_model_name == "taggedfieldtestmodel"

    def test_user_tag_with_select_related(
        self, test_user, tagged_field_factory, user_tag_factory
    ):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="ut_select_field",
        )
        ut = user_tag_factory(user=test_user, tagged_field=tfm, tags="a,b")

        fetched = UserTag.objects.select_related("tagged_field__content").get(pk=ut.pk)

        assert fetched.current_model_name == "taggedfieldtestmodel"

    def test_user_tag_falls_back_when_no_fk(self, test_user):
        """Without tagged_field FK (legacy data), falls back to cached model_name."""
        ut = UserTag.objects.create(
            user=test_user,
            tagged_field=None,
            model_name="LegacyModelName",
            field_name="legacy_field",
            tags="tag1",
        )

        assert ut.current_model_name == "LegacyModelName"

    # --- SystemTag ---

    def test_system_tag_returns_live_value(
        self, tagged_field_factory, system_tag_factory
    ):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="st_prop_field",
            model_name="StaleModelName",
            tag_type="system",
        )
        st = system_tag_factory(
            tagged_field=tfm,
            model_name="StaleSystemTagName",
            tags="sys1,sys2",
        )

        assert st.model_name == "StaleSystemTagName"
        assert st.current_model_name == "taggedfieldtestmodel"

    def test_system_tag_with_select_related(
        self, tagged_field_factory, system_tag_factory
    ):
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="st_select_field",
            tag_type="system",
        )
        st = system_tag_factory(tagged_field=tfm, tags="sys1")

        fetched = SystemTag.objects.select_related("tagged_field__content").get(
            pk=st.pk
        )

        assert fetched.current_model_name == "taggedfieldtestmodel"


# =============================================================================
# Model Schema: help_text on model_name fields
# =============================================================================


@pytest.mark.django_db
class TestModelNameFieldHelpText:
    """Verify model_name fields have help_text indicating display/cache purpose.

    Absorbed from test_model_properties.py.
    """

    @pytest.mark.parametrize(
        "model_class",
        [TaggedFieldModel, UserTag, SystemTag],
        ids=["TaggedFieldModel", "UserTag", "SystemTag"],
    )
    def test_model_name_has_help_text(self, model_class):
        field = model_class._meta.get_field("model_name")
        help_text = (field.help_text or "").lower()
        assert "display" in help_text or "cache" in help_text, (
            f"{model_class.__name__}.model_name missing help_text. "
            f"Got: '{field.help_text}'"
        )
