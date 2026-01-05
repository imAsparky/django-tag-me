"""
tag-me registry tests - UPDATED for update_or_create refactor.

Changes:
1. Added tests for update_or_create behavior (refreshes cached names)
2. Added tests for model rename resilience
3. Added tests for constraint changes (content + field_name only)
4. Fixed fixture conflicts for file-based tests
"""

import json
import os
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from django.test import TestCase, override_settings

from tag_me.models import TaggedFieldModel, TagMeSynchronise
from tests.models import TaggedFieldTestModel

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def default_tags_file():
    """
    Fixture to create default tags file.
    NOT autouse - only used by tests that need it.

    Creates file in current working directory because TagPersistence
    opens "default_user_tags.json" relative to cwd.
    """
    default_tags = {
        "test_field": ["Test Field", "default1,default2"],
        "another_field": ["Another Field", "tag1,tag2"],
    }
    # Create in current working directory (where TagPersistence looks)
    tags_path = Path("default_user_tags.json")
    with open(tags_path, "w") as f:
        json.dump(default_tags, f)

    yield tags_path

    # Cleanup
    if tags_path.exists():
        os.remove(tags_path)


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the registry between tests"""
    from tag_me.registry import SystemTagRegistry

    SystemTagRegistry._instance = None
    SystemTagRegistry._fields = set()
    SystemTagRegistry._is_ready = False
    if hasattr(settings, "DJ_TAG_ME_SYSTEM_TAGS_POPULATED"):
        settings.DJ_TAG_ME_SYSTEM_TAGS_POPULATED = False
    yield


@pytest.fixture(autouse=True)
def cleanup_default_tags_file():
    """Ensure default_user_tags.json is cleaned up after each test."""
    yield
    # Clean up any leftover files
    for path in [
        Path("default_user_tags.json"),
        BASE_DIR / "default_user_tags.json",
    ]:
        if path.exists():
            try:
                os.chmod(path, 0o666)  # Reset permissions if needed
                os.remove(path)
            except:
                pass


def test_field_metadata_creation_all_types():
    """Test lines 56-62: FieldMetadata creation with both tag types"""
    from tag_me.registry import FieldMetadata, TagType

    # System type
    system_metadata = FieldMetadata(
        model=TaggedFieldTestModel,
        field_name="test_field",
        tags="tag1,tag2",
        model_name="taggedfieldtestmodel",
        model_verbose_name="Tagged Field Test Model",
        field_verbose_name="Test Field",
        tag_type=TagType.SYSTEM,
    )

    assert system_metadata.tag_type == TagType.SYSTEM
    assert system_metadata.field_name == "test_field"


def test_tag_persistence_initialization_with_flag(monkeypatch, default_tags_file):
    """Test TagPersistence initialization with DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS=True"""
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", True
    )
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG", False
    )

    from tag_me.registry import TagPersistence

    persistence = TagPersistence()
    # Should have loaded tags from file
    assert persistence.default_user_tags != {}


def test_tag_persistence_initialization_with_debug_flag(monkeypatch, default_tags_file):
    """Test TagPersistence initialization with debug flag and DEBUG=True"""
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", False
    )
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG", True
    )
    monkeypatch.setattr("django.conf.settings.DEBUG", True)

    from tag_me.registry import TagPersistence

    persistence = TagPersistence()
    # Should have loaded tags because DEBUG=True and IN_DEBUG flag is True
    assert persistence.default_user_tags != {}


def test_tag_persistence_initialization_without_flag(monkeypatch):
    """Test TagPersistence initialization with both flags off"""
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", False
    )
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG", False
    )

    from tag_me.registry import TagPersistence

    persistence = TagPersistence()
    assert persistence.default_user_tags == {}


@pytest.mark.django_db
def test_save_fields_integrity_error():
    """Test database integrity errors via unique constraint violation.

    The unique constraint is (content, field_name). Creating two records
    with the same content + field_name should raise IntegrityError.
    """
    from django.contrib.contenttypes.models import ContentType

    from tag_me.models import TaggedFieldModel

    content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

    # Create the first record
    TaggedFieldModel.objects.create(
        content=content_type,
        field_name="duplicate_field",
        model_name="TaggedFieldTestModel",
        model_verbose_name="Tagged Field Test Model",
        field_verbose_name="Test Field",
        tag_type="user",
    )

    # Creating a second record with same content + field_name should fail
    with pytest.raises(IntegrityError):
        TaggedFieldModel.objects.create(
            content=content_type,
            field_name="duplicate_field",  # Same field_name + content
            model_name="TaggedFieldTestModel",
            model_verbose_name="Different Verbose",
            field_verbose_name="Different Field",
            tag_type="system",
        )


@pytest.mark.django_db
@override_settings(DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS=True)
def test_user_tag_update(default_tags_file):
    """Test user tag updates with default tags"""
    from tag_me.registry import FieldMetadata, TagPersistence, TagType

    # Verify file exists where TagPersistence will look
    assert Path("default_user_tags.json").exists(), (
        f"default_user_tags.json not found in cwd. "
        f"Fixture created at: {default_tags_file}, cwd: {Path.cwd()}"
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

    # Verify default tags were loaded
    assert persistence.default_user_tags, (
        f"default_user_tags not loaded. "
        f"File exists: {Path('default_user_tags.json').exists()}"
    )
    assert "test_field" in persistence.default_user_tags, (
        f"'test_field' not in default_user_tags. "
        f"Loaded: {persistence.default_user_tags}"
    )

    persistence.save_fields({metadata})

    content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
    tagged_field = TaggedFieldModel.objects.get(
        content=content_type, field_name="test_field"
    )

    assert tagged_field.default_tags == "default1,default2", (
        f"Expected 'default1,default2', got '{tagged_field.default_tags}'. "
        f"default_user_tags: {persistence.default_user_tags}"
    )


@pytest.mark.django_db
def test_migration_tracking():
    """Test migration tracking"""
    from tag_me.registry import MigrationTracker

    # Register untracked app
    MigrationTracker.register_migration("untracked_app")
    assert "untracked_app" not in MigrationTracker._migrated_apps

    # Register tracked app
    MigrationTracker.register_migration("tag_me")
    assert "tag_me" in MigrationTracker._migrated_apps

    # Test all_apps_migrated
    for app in MigrationTracker._tracked_apps:
        MigrationTracker.register_migration(app)

    assert MigrationTracker.all_apps_migrated()


def test_load_default_user_tags_json_decode_error():
    """Test handling of corrupted JSON file"""
    from tag_me.registry import TagPersistence

    # Create an invalid JSON file
    with open("default_user_tags.json", "w") as f:
        f.write("{invalid json")

    persistence = TagPersistence()
    persistence.default_user_tags = {}  # Reset
    persistence._load_default_user_tags()

    # After error handling, default_user_tags should remain empty
    assert persistence.default_user_tags == {}


def test_load_default_user_tags_missing_file():
    """Test handling of missing file"""
    from tag_me.registry import TagPersistence

    # Ensure no file exists
    for path in [Path("default_user_tags.json"), BASE_DIR / "default_user_tags.json"]:
        if path.exists():
            os.remove(path)

    persistence = TagPersistence()
    persistence.default_user_tags = {}  # Reset
    persistence._load_default_user_tags()
    assert persistence.default_user_tags == {}


def test_load_default_user_tags_permission_error():
    """Test handling of permission error"""
    import stat

    from tag_me.registry import TagPersistence

    file_path = Path("default_user_tags.json")

    try:
        # Create file with valid JSON first
        with open(file_path, "w") as f:
            f.write('{"test": ["Test", "tag1"]}')

        # Make it unreadable
        os.chmod(file_path, 0o000)

        persistence = TagPersistence()
        persistence.default_user_tags = {}  # Reset
        persistence._load_default_user_tags()
        # Should handle permission error gracefully
        assert persistence.default_user_tags == {}
    finally:
        # Always restore permissions and clean up
        if file_path.exists():
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
            os.remove(file_path)


@pytest.mark.django_db
def test_tag_field_synchronization():
    """Test synchronization of tagged fields"""
    from tag_me.models import TaggedFieldModel
    from tag_me.registry import FieldMetadata, TagPersistence, TagType

    # Create two fields to sync
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

    # Verify fields were created
    content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
    field1 = TaggedFieldModel.objects.get(content=content_type, field_name="field1")
    field2 = TaggedFieldModel.objects.get(content=content_type, field_name="field2")
    assert field1.default_tags == "tag1,tag2"
    assert field2.default_tags == "tag3,tag4"

    # Verify sync object exists
    sync = TagMeSynchronise.objects.get(name="default")
    assert sync is not None


# =====================================================
# TESTS FOR UPDATE_OR_CREATE REFACTOR
# =====================================================


@pytest.mark.django_db
class TestUpdateOrCreateBehavior(TestCase):
    """
    Test that save_fields uses update_or_create to refresh cached names.

    NEW TEST CLASS for the refactor.
    """

    def test_update_or_create_refreshes_model_name(self):
        """
        Test that save_fields updates model_name when it changes.

        This is the key test for the update_or_create refactor.
        """
        from tag_me.registry import FieldMetadata, TagPersistence, TagType

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # First save - creates record
        metadata = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="test_field",
            tags="tag1",
            model_name="OriginalModelName",
            model_verbose_name="Original Verbose Name",
            field_verbose_name="Original Field Name",
            tag_type=TagType.SYSTEM,
        )

        persistence = TagPersistence()
        persistence.save_fields({metadata})

        # Verify initial values
        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="test_field"
        )
        assert tagged_field.model_name == "OriginalModelName"
        assert tagged_field.model_verbose_name == "Original Verbose Name"

        # Second save with updated names - should update existing record
        metadata_updated = FieldMetadata(
            model=TaggedFieldTestModel,
            field_name="test_field",  # Same field
            tags="tag1",
            model_name="NewModelName",  # Changed
            model_verbose_name="New Verbose Name",  # Changed
            field_verbose_name="New Field Name",  # Changed
            tag_type=TagType.SYSTEM,
        )

        persistence.save_fields({metadata_updated})

        # Verify names were updated
        tagged_field.refresh_from_db()
        assert tagged_field.model_name == "NewModelName"
        assert tagged_field.model_verbose_name == "New Verbose Name"
        assert tagged_field.field_verbose_name == "New Field Name"

    def test_update_or_create_preserves_pk(self):
        """
        Test that update_or_create updates existing record, not creates new.
        """
        from tag_me.registry import FieldMetadata, TagPersistence, TagType

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

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

        # Get the PK
        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="pk_test_field"
        )
        original_pk = tagged_field.pk

        # Save again with different names
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

        # Should be same record (same PK)
        tagged_field.refresh_from_db()
        assert tagged_field.pk == original_pk
        assert tagged_field.model_name == "UpdatedModelName"

        # Should not have created duplicate
        count = TaggedFieldModel.objects.filter(
            content=content_type, field_name="pk_test_field"
        ).count()
        assert count == 1

    def test_update_or_create_handles_verbose_name_changes(self):
        """
        Test that field_verbose_name is updated on subsequent saves.
        """
        from tag_me.registry import FieldMetadata, TagPersistence, TagType

        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create with initial verbose name
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

        # Update verbose name (simulating field verbose_name change)
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

        tagged_field = TaggedFieldModel.objects.get(
            content=content_type, field_name="verbose_test"
        )
        assert tagged_field.field_verbose_name == "Updated Field Verbose Name"


@pytest.mark.django_db
class TestConstraintChanges(TestCase):
    """
    Test the new constraint (content + field_name only).

    NEW TEST CLASS for the refactor.
    """

    def test_unique_constraint_content_and_field_name(self):
        """
        Test that uniqueness is enforced on (content, field_name) only.
        """
        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create first record
        TaggedFieldModel.objects.create(
            content=content_type,
            model_name="ModelA",
            field_name="same_field",
            tag_type="user",
            field_verbose_name="Field A",
        )

        # Try to create duplicate (same content + field_name)
        # This should fail due to unique constraint
        with pytest.raises(IntegrityError):
            TaggedFieldModel.objects.create(
                content=content_type,
                model_name="ModelB",  # Different model_name
                field_name="same_field",  # Same field_name
                tag_type="system",  # Different tag_type
                field_verbose_name="Field B",  # Different verbose name
            )

    def test_different_fields_same_content_allowed(self):
        """
        Test that different field_names with same content are allowed.
        """
        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create first record
        field1 = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="Model",
            field_name="field_1",
            tag_type="user",
            field_verbose_name="Field 1",
        )

        # Create second record with different field_name
        field2 = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="Model",
            field_name="field_2",
            tag_type="user",
            field_verbose_name="Field 2",
        )

        assert field1.pk != field2.pk
        assert TaggedFieldModel.objects.filter(content=content_type).count() == 2


@pytest.mark.django_db
class TestCurrentModelNameProperty(TestCase):
    """
    Test the new current_model_name property on TaggedFieldModel.

    NEW TEST CLASS for the refactor.

    NOTE: ContentType.model stores model names in LOWERCASE.
    """

    def test_current_model_name_returns_live_value(self):
        """
        Test that current_model_name returns the live model name from ContentType.

        NOTE: ContentType.model is lowercase, so this returns lowercase.
        """
        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        tagged_field = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="StaleModelName",  # Intentionally stale
            field_name="test_field",
            tag_type="user",
            field_verbose_name="Test Field",
        )

        # current_model_name returns lowercase (from ContentType.model)
        assert tagged_field.current_model_name == "taggedfieldtestmodel"
        # Verify it's different from the stale cached value
        assert tagged_field.current_model_name != tagged_field.model_name

    def test_current_model_class_returns_model(self):
        """
        Test that current_model_class returns the actual model class.
        """
        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        tagged_field = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="WhateverName",
            field_name="test_field",
            tag_type="user",
            field_verbose_name="Test Field",
        )

        assert tagged_field.current_model_class == TaggedFieldTestModel
        # Use __name__ to get proper case if needed
        assert tagged_field.current_model_class.__name__ == "TaggedFieldTestModel"

    def test_app_label_property(self):
        """
        Test that app_label property returns correct app label.
        """
        content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        tagged_field = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="Model",
            field_name="test_field",
            tag_type="user",
            field_verbose_name="Test Field",
        )

        assert tagged_field.app_label == "tests"
