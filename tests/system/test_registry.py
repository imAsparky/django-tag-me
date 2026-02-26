"""
Tests for tag_me.registry module.

Covers:
    - FieldMetadata dataclass creation
    - TagPersistence initialization and file loading
    - TagPersistence.save_fields (update_or_create behavior)
    - TaggedFieldModel unique constraints and properties
    - MigrationTracker singleton behavior

All tests are pytest-style (no Django TestCase) so that conftest.py
autouse fixtures (reset_registry) apply consistently.
"""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError

from tag_me.models import TaggedFieldModel, TagMeSynchronise
from tag_me.registry import FieldMetadata, TagPersistence, TagType
from tests.models import TaggedFieldTestModel

# =============================================================================
# FieldMetadata
# =============================================================================


class TestFieldMetadata:
    """Test FieldMetadata dataclass creation."""

    def test_system_type(self):
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="test_field",
            tags="tag1,tag2",
            model_name="taggedfieldtestmodel",
            model_verbose_name="Tagged Field Test Model",
            field_verbose_name="Test Field",
            tag_type=TagType.SYSTEM,
        )

        assert metadata.tag_type == TagType.SYSTEM
        assert metadata.field_name == "test_field"
        assert metadata.tags == "tag1,tag2"

    def test_user_type(self):
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="user_field",
            tags="",
            model_name="taggedfieldtestmodel",
            model_verbose_name="Tagged Field Test Model",
            field_verbose_name="User Field",
            tag_type=TagType.USER,
        )

        assert metadata.tag_type == TagType.USER
        assert metadata.tags == ""


# =============================================================================
# TagPersistence Initialization
# =============================================================================


class TestTagPersistenceInit:
    """Test TagPersistence constructor and file loading behavior.

    These tests exercise the public interface (constructor) rather than
    calling _load_default_user_tags directly.
    """

    def test_loads_tags_when_seed_flag_enabled(self, monkeypatch, default_tags_file):
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", True
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG",
            False,
        )

        persistence = TagPersistence()

        assert "test_field" in persistence.default_user_tags
        assert "another_field" in persistence.default_user_tags

    def test_loads_tags_when_debug_flag_enabled(self, monkeypatch, default_tags_file):
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", False
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG",
            True,
        )

        persistence = TagPersistence()

        assert persistence.default_user_tags != {}

    def test_skips_loading_when_flags_disabled(self, monkeypatch):
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", False
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG",
            False,
        )

        persistence = TagPersistence()

        assert persistence.default_user_tags == {}

    def test_handles_corrupted_json_gracefully(self, tmp_path, monkeypatch):
        """Constructor should not raise on invalid JSON — logs and continues."""
        bad_file = tmp_path / "default_user_tags.json"
        bad_file.write_text("{invalid json")
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_DEFAULT_TAGS_FILE", str(bad_file)
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", True
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG",
            False,
        )

        persistence = TagPersistence()

        assert persistence.default_user_tags == {}

    def test_handles_missing_file_gracefully(self, tmp_path, monkeypatch):
        """Constructor should not raise when file doesn't exist — logs and continues."""
        nonexistent = tmp_path / "does_not_exist.json"
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_DEFAULT_TAGS_FILE", str(nonexistent)
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", True
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG",
            False,
        )

        persistence = TagPersistence()

        assert persistence.default_user_tags == {}


# =============================================================================
# TagPersistence.save_fields
# =============================================================================


@pytest.mark.django_db
class TestSaveFields:
    """Test save_fields behavior including update_or_create semantics."""

    def test_creates_system_tag_field(self):
        """save_fields should create a TaggedFieldModel with correct default_tags."""
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="field1",
            tags="tag1,tag2",
            model_name="taggedfieldtestmodel",
            model_verbose_name="Test Model",
            field_verbose_name="Field 1",
            tag_type=TagType.SYSTEM,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata})

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        field = TaggedFieldModel.objects.get(content=content_type, field_name="field1")
        assert field.default_tags == "tag1,tag2"

    def test_synchronization_creates_fields_and_sync_object(self):
        """save_fields should create multiple fields and a TagMeSynchronise record."""
        metadata1 = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="field1",
            tags="tag1,tag2",
            model_name="taggedfieldtestmodel",
            model_verbose_name="Test Model",
            field_verbose_name="Field 1",
            tag_type=TagType.SYSTEM,
        )
        metadata2 = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="field2",
            tags="tag3,tag4",
            model_name="taggedfieldtestmodel",
            model_verbose_name="Test Model",
            field_verbose_name="Field 2",
            tag_type=TagType.SYSTEM,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata1, metadata2})

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        # Assert the specific records we created exist (the model may have
        # additional TaggedFieldModel records from real TagMeCharField fields
        # registered during post-migrate)
        assert TaggedFieldModel.objects.filter(
            content=content_type, field_name="field1"
        ).exists()
        assert TaggedFieldModel.objects.filter(
            content=content_type, field_name="field2"
        ).exists()
        assert TagMeSynchronise.objects.filter(name="default").exists()

    def test_applies_default_user_tags_on_create(self, monkeypatch, default_tags_file):
        """save_fields should apply default user tags when creating a new field."""
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", True
        )
        monkeypatch.setattr(
            "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG",
            False,
        )

        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="test_field",
            tags="",
            model_name="taggedfieldtestmodel",
            model_verbose_name="Tagged Field Test Model",
            field_verbose_name="Test Field",
            tag_type=TagType.USER,
        )

        persistence = TagPersistence()
        assert "test_field" in persistence.default_user_tags
        persistence.save_fields({metadata})

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="test_field"
        )
        assert tagged_field.default_tags == "default1,default2"


# =============================================================================
# update_or_create Behavior
# =============================================================================


@pytest.mark.django_db
class TestUpdateOrCreateBehavior:
    """Test that save_fields uses update_or_create to refresh cached names.

    These tests verify the refactor from get_or_create to update_or_create,
    ensuring display fields are refreshed on each migration while the
    lookup key (content + field_name) stays stable.
    """

    def test_refreshes_model_name_on_update(self):
        """Second save with changed names should update existing record."""
        metadata_v1 = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="test_field",
            tags="tag1",
            model_name="OriginalModelName",
            model_verbose_name="Original Verbose Name",
            field_verbose_name="Original Field Name",
            tag_type=TagType.SYSTEM,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata_v1})

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="test_field"
        )
        assert tagged_field.model_name == "OriginalModelName"

        metadata_v2 = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="test_field",
            tags="tag1",
            model_name="NewModelName",
            model_verbose_name="New Verbose Name",
            field_verbose_name="New Field Name",
            tag_type=TagType.SYSTEM,
        )

        persistence.save_fields({metadata_v2})

        tagged_field.refresh_from_db()
        assert tagged_field.model_name == "NewModelName"
        assert tagged_field.model_verbose_name == "New Verbose Name"
        assert tagged_field.field_verbose_name == "New Field Name"

    def test_preserves_pk_on_update(self):
        """update_or_create should modify the existing row, not create a new one."""
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="pk_test_field",
            tags="tag1",
            model_name="ModelName",
            model_verbose_name="Verbose Name",
            field_verbose_name="Field Name",
            tag_type=TagType.SYSTEM,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata})

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        original_pk = TaggedFieldModel.objects.get(
            content=content_type, field_name="pk_test_field"
        ).pk

        metadata_updated = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="pk_test_field",
            tags="tag1",
            model_name="UpdatedModelName",
            model_verbose_name="Updated Verbose Name",
            field_verbose_name="Updated Field Name",
            tag_type=TagType.SYSTEM,
        )

        persistence.save_fields({metadata_updated})

        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="pk_test_field"
        )
        assert tagged_field.pk == original_pk
        assert tagged_field.model_name == "UpdatedModelName"
        assert (
            TaggedFieldModel.objects.filter(
                content=content_type, field_name="pk_test_field"
            ).count()
            == 1
        )

    def test_updates_verbose_name_on_change(self):
        """field_verbose_name should be updated on subsequent saves."""
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="verbose_test",
            tags="",
            model_name="Model",
            model_verbose_name="Model Verbose",
            field_verbose_name="Initial Field Verbose Name",
            tag_type=TagType.USER,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata})

        metadata_updated = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="verbose_test",
            tags="",
            model_name="Model",
            model_verbose_name="Model Verbose",
            field_verbose_name="Updated Field Verbose Name",
            tag_type=TagType.USER,
        )

        persistence.save_fields({metadata_updated})

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="verbose_test"
        )
        assert tagged_field.field_verbose_name == "Updated Field Verbose Name"


# =============================================================================
# Unique Constraints
# =============================================================================


@pytest.mark.django_db
class TestConstraints:
    """Test unique constraint on (content, field_name)."""

    def test_duplicate_content_and_field_name_raises(self, tagged_field_factory):
        """Two records with same content + field_name should violate the constraint."""
        tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="duplicate_field",
        )

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        with pytest.raises(IntegrityError):
            TaggedFieldModel.objects.create(
                content=content_type,
                field_name="duplicate_field",
                model_name="Different",
                model_verbose_name="Different",
                field_verbose_name="Different",
                tag_type="system",
            )

    def test_different_fields_same_content_allowed(self, tagged_field_factory):
        """Different field_names with the same content should coexist."""
        field1 = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="field_1",
        )
        field2 = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="field_2",
        )

        assert field1.pk != field2.pk
        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
        assert (
            TaggedFieldModel.objects.filter(
                content=content_type, field_name__in=["field_1", "field_2"]
            ).count()
            == 2
        )


# =============================================================================
# TaggedFieldModel Properties
# =============================================================================


@pytest.mark.django_db
class TestTaggedFieldModelProperties:
    """Test computed properties on TaggedFieldModel.

    Note: ContentType.model stores model names in lowercase.
    """

    def test_current_model_name_returns_live_value(self, tagged_field_factory):
        """current_model_name should read from ContentType, not the cached field."""
        tagged_field = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="test_field",
            model_name="StaleModelName",
        )

        assert tagged_field.current_model_name == "taggedfieldtestmodel"
        assert tagged_field.current_model_name != tagged_field.model_name

    def test_current_model_class_returns_model(self, tagged_field_factory):
        """current_model_class should return the actual Django model class."""
        tagged_field = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="test_field",
            model_name="WhateverName",
        )

        assert tagged_field.current_model_class == TaggedFieldTestModel
        assert tagged_field.current_model_class.__name__ == "TaggedFieldTestModel"

    def test_app_label_property(self, tagged_field_factory):
        """app_label should return the correct app label from ContentType."""
        tagged_field = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="test_field",
        )

        assert tagged_field.app_label == "tests"


# =============================================================================
# MigrationTracker
# =============================================================================


@pytest.mark.django_db
class TestMigrationTracker:
    """Test MigrationTracker singleton behavior."""

    def test_ignores_untracked_apps(self):
        """Apps not in the tracked set should not be recorded."""
        from tag_me.registry import MigrationTracker

        # Use a known tracked set to isolate from app registry state
        MigrationTracker._tracked_apps = {"tag_me", "contenttypes"}

        MigrationTracker.register_migration("untracked_app")

        assert "untracked_app" not in MigrationTracker._migrated_apps

    def test_tracks_known_app(self):
        """Apps in the tracked set should be added to _migrated_apps."""
        from tag_me.registry import MigrationTracker

        MigrationTracker._tracked_apps = {"tag_me", "contenttypes"}

        MigrationTracker.register_migration("tag_me")

        assert "tag_me" in MigrationTracker._migrated_apps

    def test_reports_all_migrated_when_complete(self):
        """all_apps_migrated returns True only when every tracked app is registered."""
        from tag_me.registry import MigrationTracker

        MigrationTracker._tracked_apps = {"app_a", "app_b"}

        MigrationTracker.register_migration("app_a")
        assert not MigrationTracker.all_apps_migrated()

        MigrationTracker.register_migration("app_b")
        assert MigrationTracker.all_apps_migrated()
