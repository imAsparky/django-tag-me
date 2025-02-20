import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.conf import settings
from tag_me.models import TaggedFieldModel, TagMeSynchronise
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from tests.models import TaggedFieldTestModel
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def setup_default_tags():
    """Setup and teardown for default tags file"""
    # Create default tags file
    default_tags = {
        "test_field": ["Test Field", "default1,default2"],
        "another_field": ["Another Field", "tag1,tag2"],
    }
    tags_path = BASE_DIR / "default_user_tags.json"
    with open(tags_path, "w") as f:
        json.dump(default_tags, f)

    yield

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
    settings.DJ_TAG_ME_SYSTEM_TAGS_POPULATED = False
    yield


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


def test_tag_persistence_initialization_with_flag(monkeypatch):
    """Test lines 86-89: TagPersistence initialization with flag off"""
    # Need to monkeypatch the setting before importing
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", True
    )
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG", False
    )

    from tag_me.registry import TagPersistence

    persistence = TagPersistence()
    assert persistence.default_user_tags != {}


def test_tag_persistence_initialization_with_debug_flag(monkeypatch):
    """Test lines 86-89: TagPersistence initialization with flag off and debug on"""
    # Need to monkeypatch the setting before importing
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS", False
    )
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS_IN_DEBUG", True
    )

    from tag_me.registry import TagPersistence

    persistence = TagPersistence()
    assert persistence.default_user_tags != {}


def test_tag_persistence_initialization_without_flag(monkeypatch):
    """Test lines 86-89: TagPersistence initialization with flag off"""
    # Need to monkeypatch the setting before importing
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
    """Test lines 147-165: Database integrity errors"""
    from tag_me.registry import TagPersistence, FieldMetadata, TagType

    # Create metadata with field that will fail integrity check
    metadata = FieldMetadata(
        model=TaggedFieldTestModel,
        field_name=None,  # This will cause IntegrityError
        tags="tag1,tag2",
        model_name="taggedfieldtestmodel",
        model_verbose_name="Tagged Field Test Model",
        field_verbose_name="Test Field",
        tag_type=TagType.SYSTEM,
    )

    persistence = TagPersistence()
    with pytest.raises(IntegrityError):
        persistence.save_fields({metadata})


@pytest.mark.django_db
@override_settings(DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS=True)
def test_user_tag_update():
    """Test lines 206, 211-212: User tag updates"""
    from tag_me.registry import TagPersistence, FieldMetadata, TagType

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
    persistence.save_fields({metadata})

    content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)
    tagged_field = TaggedFieldModel.objects.get(
        content=content_type, field_name="test_field"
    )

    assert tagged_field.default_tags == "default1,default2"


@pytest.mark.django_db
def test_migration_tracking():
    """Test lines 288-291: Migration tracking"""
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


# NOTE: Additional
@pytest.mark.django_db
def test_load_default_user_tags_json_decode_error(tmp_path):
    """Test handling of corrupted JSON file"""
    from tag_me.registry import TagPersistence
    import json

    # Create an invalid JSON file
    tags_path = tmp_path / "default_user_tags.json"
    tags_path.write_text("{invalid json")

    persistence = TagPersistence()
    persistence.default_user_tags = {}  # Reset default tags

    # Force reload with invalid file
    with override_settings(DEFAULT_USER_TAGS_PATH=str(tags_path)):
        persistence._load_default_user_tags()
        assert persistence.default_user_tags == {}


def test_load_default_user_tags_json_decode_error(tmp_path, monkeypatch):
    """Test handling of corrupted JSON file"""
    from tag_me.registry import TagPersistence

    # Create an invalid JSON file
    with open("default_user_tags.json", "w") as f:
        f.write("{invalid json")

    try:
        persistence = TagPersistence()
        persistence._load_default_user_tags()
        # After error handling, default_user_tags should remain empty
        assert persistence.default_user_tags == {}
    finally:
        # Clean up our test file
        import os

        os.remove("default_user_tags.json")


def test_load_default_user_tags_missing_file():
    """Test handling of missing file"""
    from tag_me.registry import TagPersistence
    import os

    # Ensure the file doesn't exist
    if os.path.exists("default_user_tags.json"):
        os.remove("default_user_tags.json")

    persistence = TagPersistence()
    persistence._load_default_user_tags()
    assert persistence.default_user_tags == {}


def test_load_default_user_tags_permission_error(monkeypatch):
    """Test handling of permission error"""
    from tag_me.registry import TagPersistence
    import os

    # Create file with no read permissions
    with open("default_user_tags.json", "w") as f:
        f.write("{}")
    os.chmod("default_user_tags.json", 0o000)

    try:
        persistence = TagPersistence()
        persistence._load_default_user_tags()
        assert persistence.default_user_tags == {}
    finally:
        # Reset permissions so we can clean up
        os.chmod("default_user_tags.json", 0o666)
        os.remove("default_user_tags.json")


@pytest.mark.django_db
def test_tag_field_synchronization():
    """Test synchronization of tagged fields"""
    from tag_me.registry import TagPersistence, FieldMetadata, TagType
    from tag_me.models import TagMeSynchronise, TaggedFieldModel

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
