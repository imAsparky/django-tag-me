"""
Global pytest fixtures for django-tag-me tests.

Fixtures here are available to ALL test files under tests/.

What Belongs Here
=================
    ✓ Registry reset (autouse)
    ✓ Common model factories used across multiple test files
    ✓ Shared file-based fixtures (default_tags_file)

What Does NOT Belong Here
=========================
    ✗ Fixtures specific to a single test file
"""

import json

import pytest

# =============================================================================
# Registry Reset
# =============================================================================


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset SystemTagRegistry between tests.

    The registry stores class-level state that persists across tests.
    Without this reset, tests can see stale fields, readiness flags,
    or population state from previous tests.
    """
    from tag_me.registry import SystemTagRegistry

    SystemTagRegistry.reset()

    yield

    SystemTagRegistry.reset()


# =============================================================================
# File-Based Fixtures
# =============================================================================


@pytest.fixture
def default_tags_file(tmp_path, monkeypatch):
    """Create a default user tags JSON file in an isolated tmp directory.

    Uses tmp_path (unique per test, cleaned up by pytest) and monkeypatches
    DJ_TAG_ME_DEFAULT_TAGS_FILE to point at it. Parallel-safe — no shared
    filesystem state.

    The seed flag is NOT enabled here — individual tests should enable
    DJ_TAG_ME_SEED_INITIAL_USER_DEFAULT_TAGS or the debug variant as needed.
    This keeps the fixture composable.
    """
    tags_path = tmp_path / "default_user_tags.json"
    default_tags = {
        "test_field": ["Test Field", "default1,default2"],
        "another_field": ["Another Field", "tag1,tag2"],
    }
    tags_path.write_text(json.dumps(default_tags))
    monkeypatch.setattr(
        "django.conf.settings.DJ_TAG_ME_DEFAULT_TAGS_FILE",
        str(tags_path),
    )
    return tags_path


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def test_user_factory(db):
    """Factory for creating test users with automatic cleanup.

    Usage:
        def test_something(test_user_factory):
            user1 = test_user_factory(username="alice")
            user2 = test_user_factory(username="bob")
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    created = []

    def _factory(
        username="testuser",
        email="",
        password="testpass123",
        **kwargs,
    ):
        user = User.objects.create_user(
            username=username,
            email=email or f"{username}@example.com",
            password=password,
            **kwargs,
        )
        created.append(user)
        return user

    yield _factory

    for user in reversed(created):
        try:
            user.delete()
        except Exception:
            pass


@pytest.fixture
def test_user(test_user_factory):
    """Convenience: a default test user."""
    return test_user_factory(username="testuser")


# =============================================================================
# Model Factories
# =============================================================================


@pytest.fixture
def tagged_field_factory(db):
    """Factory for TaggedFieldModel with automatic cleanup.

    Accepts either model_class (for real models) or content_type (for
    fake/isolated ContentTypes). When content_type is provided, model_class
    is ignored.

    Usage:
        # With a real model:
        field = tagged_field_factory(model_class=MyModel, field_name="my_field")

        # With a fake ContentType (for isolated tests):
        ct = ContentType.objects.get_or_create(app_label="tests", model="fake")[0]
        field = tagged_field_factory(
            content_type=ct, field_name="my_field", model_name="FakeModel"
        )

    Cleanup runs even if the test fails. Records are deleted in
    reverse creation order to respect foreign key constraints.
    """
    from django.contrib.contenttypes.models import ContentType

    from tag_me.models import TaggedFieldModel

    created = []

    def _factory(
        field_name,
        model_class=None,
        content_type=None,
        model_name="",
        model_verbose_name="",
        field_verbose_name="",
        tag_type="user",
        default_tags="",
    ):
        if content_type is None:
            if model_class is None:
                raise ValueError("Provide either model_class or content_type")
            content_type = ContentType.objects.get_for_model(model_class)
            model_name = model_name or model_class.__name__
            model_verbose_name = model_verbose_name or str(
                model_class._meta.verbose_name
            )
        else:
            model_name = model_name or content_type.model
            model_verbose_name = model_verbose_name or model_name

        obj = TaggedFieldModel.objects.create(
            content=content_type,
            field_name=field_name,
            model_name=model_name,
            model_verbose_name=model_verbose_name,
            field_verbose_name=field_verbose_name or field_name,
            tag_type=tag_type,
            default_tags=default_tags,
        )
        created.append(obj)
        return obj

    yield _factory

    for obj in reversed(created):
        try:
            obj.delete()
        except Exception:
            pass


@pytest.fixture
def stale_content_type_factory(db):
    """Factory for creating ContentType entries that point to nonexistent models.

    model_class() returns None for these entries, which is exactly what
    happens when a Django model is deleted or renamed via DeleteModel +
    CreateModel (instead of RenameModel).

    Usage:
        def test_orphan_detection(stale_content_type_factory):
            stale_ct = stale_content_type_factory(model="deletedmodel")
            assert stale_ct.model_class() is None
    """
    from django.contrib.contenttypes.models import ContentType

    created = []

    def _factory(app_label="tests", model="deletedmodel"):
        ct = ContentType.objects.create(
            app_label=app_label,
            model=model,
        )
        created.append(ct)
        return ct

    yield _factory

    for obj in reversed(created):
        try:
            obj.delete()
        except Exception:
            pass


@pytest.fixture
def user_tag_factory(db):
    """Factory for UserTag with automatic cleanup.

    Creates UserTag records linked to a TaggedFieldModel and user.
    The slug is auto-generated by TagBase.save().

    Usage:
        def test_something(user_tag_factory, tagged_field_factory, test_user):
            tfm = tagged_field_factory(model_class=MyModel, field_name="field")
            ut = user_tag_factory(
                user=test_user,
                tagged_field=tfm,
                tags="tag1,tag2",
            )
    """
    from tag_me.models import UserTag

    created = []

    def _factory(
        user,
        tagged_field,
        tags="",
        field_name="",
        model_name="",
        model_verbose_name="",
        field_verbose_name="",
        search_tags="",
    ):
        obj = UserTag(
            user=user,
            tagged_field=tagged_field,
            tags=tags,
            field_name=field_name or tagged_field.field_name,
            model_name=model_name or tagged_field.model_name,
            model_verbose_name=model_verbose_name or tagged_field.model_verbose_name,
            field_verbose_name=field_verbose_name or tagged_field.field_verbose_name,
            search_tags=search_tags,
        )
        # Use sync_tags_save=True to skip tag synchronization during tests
        obj.save(sync_tags_save=True)
        created.append(obj)
        return obj

    yield _factory

    for obj in reversed(created):
        try:
            obj.delete()
        except Exception:
            pass


@pytest.fixture
def system_tag_factory(db):
    """Factory for SystemTag with automatic cleanup.

    Creates SystemTag records linked to a TaggedFieldModel.
    The slug is auto-generated by TagBase.save().

    Note: There is a unique constraint — only one SystemTag per
    TaggedFieldModel (when tagged_field is not null).

    Usage:
        def test_something(system_tag_factory, tagged_field_factory):
            tfm = tagged_field_factory(model_class=MyModel, field_name="field")
            st = system_tag_factory(tagged_field=tfm, tags="sys1,sys2")
    """
    from tag_me.models import SystemTag

    created = []

    def _factory(
        tagged_field,
        tags="",
        field_name="",
        model_name="",
        model_verbose_name="",
        field_verbose_name="",
        search_tags="",
    ):
        obj = SystemTag(
            tagged_field=tagged_field,
            tags=tags,
            field_name=field_name or tagged_field.field_name,
            model_name=model_name or tagged_field.model_name,
            model_verbose_name=model_verbose_name or tagged_field.model_verbose_name,
            field_verbose_name=field_verbose_name or tagged_field.field_verbose_name,
            search_tags=search_tags,
        )
        obj.save()
        created.append(obj)
        return obj

    yield _factory

    for obj in reversed(created):
        try:
            obj.delete()
        except Exception:
            pass
