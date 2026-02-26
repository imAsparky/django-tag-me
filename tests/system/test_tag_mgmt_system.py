"""
Tests for tag_me/utils/tag_mgmt_system.py

Covers:
    - populate_all_tag_records() orchestrator
    - _populate_system_tags()
    - populate_user_tags()
    - update_fields_that_should_be_synchronised()
    - Integration: full population workflow, incremental population

All tests are pytest-style. Test-specific fixtures use a fake ContentType
("tagmgmttestmodel") to isolate from real TagMeCharField registrations
that happen during post-migrate.

Run with: pytest tests/test_tag_mgmt_system.py -v
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import DatabaseError, DataError, IntegrityError

from tag_me.models import (
    SystemTag,
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.utils.tag_mgmt_system import (
    _populate_system_tags,
    populate_all_tag_records,
    populate_user_tags,
    update_fields_that_should_be_synchronised,
)

User = get_user_model()


# =============================================================================
# Test-Specific Fixtures
#
# These use a fake ContentType ("tagmgmttestmodel") that doesn't map to a
# real Django model. This intentionally isolates test data from the real
# TaggedFieldModel records created by post-migrate field registration.
# =============================================================================


@pytest.fixture
def fake_content_type(db):
    """An isolated ContentType that doesn't map to any real model.

    This ensures counts and queries in tests are not affected by
    real TagMeCharField registrations on actual models.
    """
    ct, _ = ContentType.objects.get_or_create(
        app_label="tests",
        model="tagmgmttestmodel",
    )
    yield ct


@pytest.fixture
def user_tagged_field(fake_content_type):
    """A user-type TaggedFieldModel for testing population logic."""
    obj = TaggedFieldModel.objects.create(
        content=fake_content_type,
        model_name="TagMgmtTestModel",
        model_verbose_name="Tag Mgmt Test Model",
        field_name="user_tags_field",
        field_verbose_name="User Tags Field",
        tag_type="user",
        default_tags="",
    )
    yield obj
    try:
        obj.delete()
    except Exception:
        pass


@pytest.fixture
def system_tagged_field(fake_content_type):
    """A system-type TaggedFieldModel with default tags."""
    obj = TaggedFieldModel.objects.create(
        content=fake_content_type,
        model_name="TagMgmtTestModel",
        model_verbose_name="Tag Mgmt Test Model",
        field_name="system_tags_field",
        field_verbose_name="System Tags Field",
        tag_type="system",
        default_tags="option1,option2,option3,",
    )
    yield obj
    try:
        obj.delete()
    except Exception:
        pass


@pytest.fixture
def system_tagged_field_no_defaults(fake_content_type):
    """A system-type TaggedFieldModel without default tags."""
    obj = TaggedFieldModel.objects.create(
        content=fake_content_type,
        model_name="TagMgmtTestModel",
        model_verbose_name="Tag Mgmt Test Model",
        field_name="system_tags_empty",
        field_verbose_name="System Tags Empty",
        tag_type="system",
        default_tags="",
    )
    yield obj
    try:
        obj.delete()
    except Exception:
        pass


# =============================================================================
# populate_all_tag_records
# =============================================================================


@pytest.mark.django_db
class TestPopulateAllTagRecords:
    """Tests for the main orchestrator function."""

    def test_populates_system_and_user_tags(
        self, test_user, user_tagged_field, system_tagged_field
    ):
        """Should create both SystemTag and UserTag records."""
        populate_all_tag_records()

        assert SystemTag.objects.filter(tagged_field=system_tagged_field).exists()
        assert UserTag.objects.filter(
            user=test_user, tagged_field=user_tagged_field
        ).exists()

    def test_populates_for_specific_user_only(
        self, test_user_factory, user_tagged_field
    ):
        """When user arg is provided, only that user gets tags."""
        user1 = test_user_factory(username="pop_user1")
        user2 = test_user_factory(username="pop_user2")

        populate_all_tag_records(user=user1)

        assert UserTag.objects.filter(
            user=user1, tagged_field=user_tagged_field
        ).exists()
        assert not UserTag.objects.filter(
            user=user2, tagged_field=user_tagged_field
        ).exists()

    def test_reraises_exceptions_after_logging(self, user_tagged_field):
        """Exceptions from sub-functions should propagate."""
        with patch("tag_me.utils.tag_mgmt_system._populate_system_tags") as mock_sys:
            mock_sys.side_effect = ValidationError("Test error")

            with pytest.raises(ValidationError, match="Test error"):
                populate_all_tag_records()

    def test_idempotent_on_repeated_calls(
        self, test_user, user_tagged_field, system_tagged_field
    ):
        """Running twice should not create duplicate records."""
        populate_all_tag_records()

        user_tag_count = UserTag.objects.filter(tagged_field=user_tagged_field).count()
        system_tag_count = SystemTag.objects.filter(
            tagged_field=system_tagged_field
        ).count()

        populate_all_tag_records()

        assert (
            UserTag.objects.filter(tagged_field=user_tagged_field).count()
            == user_tag_count
        )
        assert (
            SystemTag.objects.filter(tagged_field=system_tagged_field).count()
            == system_tag_count
        )


# =============================================================================
# _populate_system_tags
# =============================================================================


@pytest.mark.django_db
class TestPopulateSystemTags:
    """Tests for _populate_system_tags function."""

    def test_creates_system_tag_with_default_tags(self, system_tagged_field):
        """Should create a SystemTag with tags from default_tags."""
        _populate_system_tags()

        system_tag = SystemTag.objects.get(tagged_field=system_tagged_field)
        assert system_tag.tags == system_tagged_field.default_tags
        assert system_tag.field_name == system_tagged_field.field_name
        assert system_tag.model_name == system_tagged_field.model_name

    def test_skips_field_without_default_tags(self, system_tagged_field_no_defaults):
        """Should not create a SystemTag when default_tags is empty."""
        _populate_system_tags()

        assert not SystemTag.objects.filter(
            tagged_field=system_tagged_field_no_defaults
        ).exists()

    def test_updates_existing_system_tag_on_rerun(self, system_tagged_field):
        """Should update (not duplicate) when tags change."""
        _populate_system_tags()

        original_tag = SystemTag.objects.get(tagged_field=system_tagged_field)
        original_pk = original_tag.pk

        system_tagged_field.default_tags = "new1,new2,new3,"
        system_tagged_field.save()

        _populate_system_tags()

        updated_tag = SystemTag.objects.get(tagged_field=system_tagged_field)
        assert updated_tag.pk == original_pk
        assert updated_tag.tags == "new1,new2,new3,"

    def test_no_system_fields_does_not_raise(self, user_tagged_field):
        """Should handle case where only user fields exist."""
        _populate_system_tags()

        assert not SystemTag.objects.filter(tagged_field=user_tagged_field).exists()

    def test_raises_validation_error_on_integrity_error(self, system_tagged_field):
        with patch.object(SystemTag.objects, "update_or_create") as mock_uoc:
            mock_uoc.side_effect = IntegrityError("Duplicate key")

            with pytest.raises(ValidationError, match="Duplicate system tag"):
                _populate_system_tags()

    def test_raises_validation_error_on_data_error(self, system_tagged_field):
        with patch.object(SystemTag.objects, "update_or_create") as mock_uoc:
            mock_uoc.side_effect = DataError("Invalid data")

            with pytest.raises(ValidationError, match="Invalid data type"):
                _populate_system_tags()

    def test_raises_validation_error_on_database_error(self, system_tagged_field):
        with patch.object(SystemTag.objects, "update_or_create") as mock_uoc:
            mock_uoc.side_effect = DatabaseError("Connection failed")

            with pytest.raises(ValidationError, match="Database error"):
                _populate_system_tags()


# =============================================================================
# populate_user_tags
# =============================================================================


@pytest.mark.django_db
class TestPopulateUserTags:
    """Tests for populate_user_tags function."""

    def test_creates_user_tag_for_each_user_field_combo(
        self, test_user_factory, user_tagged_field
    ):
        """Should create a UserTag for every user × user-field combination."""
        user1 = test_user_factory(username="utag_user1")
        user2 = test_user_factory(username="utag_user2")

        populate_user_tags()

        assert UserTag.objects.filter(
            user=user1, tagged_field=user_tagged_field
        ).exists()
        assert UserTag.objects.filter(
            user=user2, tagged_field=user_tagged_field
        ).exists()

    def test_specific_user_only_creates_for_that_user(
        self, test_user_factory, user_tagged_field
    ):
        """Should only create for the specified user."""
        user1 = test_user_factory(username="specific_user1")
        user2 = test_user_factory(username="specific_user2")

        populate_user_tags(user=user1)

        assert UserTag.objects.filter(
            user=user1, tagged_field=user_tagged_field
        ).exists()
        assert not UserTag.objects.filter(
            user=user2, tagged_field=user_tagged_field
        ).exists()

    def test_skips_users_with_existing_tags(self, test_user, user_tagged_field):
        """Should not overwrite existing UserTag records."""
        existing = UserTag(
            user=test_user,
            tagged_field=user_tagged_field,
            model_name="TagMgmtTestModel",
            field_name="user_tags_field",
            tags="existing_tag,",
        )
        existing.save(sync_tags_save=True)

        populate_user_tags()

        existing.refresh_from_db()
        assert existing.tags == "existing_tag,"
        assert (
            UserTag.objects.filter(
                user=test_user, tagged_field=user_tagged_field
            ).count()
            == 1
        )

    def test_creates_tags_for_new_field_on_existing_user(
        self, test_user, fake_content_type
    ):
        """Adding a new field should create UserTags for existing users."""
        field1 = TaggedFieldModel.objects.create(
            content=fake_content_type,
            model_name="TagMgmtTestModel",
            field_name="existing_field",
            field_verbose_name="Existing Field",
            tag_type="user",
        )

        # Pre-create a tag for field1
        ut = UserTag(
            user=test_user,
            tagged_field=field1,
            model_name="TagMgmtTestModel",
            field_name="existing_field",
            tags="existing,",
        )
        ut.save(sync_tags_save=True)

        # Add a new field
        field2 = TaggedFieldModel.objects.create(
            content=fake_content_type,
            model_name="TagMgmtTestModel",
            field_name="new_field",
            field_verbose_name="New Field",
            tag_type="user",
        )

        populate_user_tags(user=test_user)

        # New field should have a UserTag
        assert UserTag.objects.filter(user=test_user, tagged_field=field2).exists()

        # Original tag should be unchanged
        ut.refresh_from_db()
        assert ut.tags == "existing,"

    def test_no_user_fields_does_not_create_tags(self, test_user, system_tagged_field):
        """Should not create UserTags for system-type fields."""
        populate_user_tags()

        assert not UserTag.objects.filter(tagged_field=system_tagged_field).exists()

    def test_no_users_creates_nothing(self, user_tagged_field):
        """Should handle the case where no users exist."""
        User.objects.all().delete()

        populate_user_tags()

        assert not UserTag.objects.filter(tagged_field=user_tagged_field).exists()

    def test_raises_validation_error_on_integrity_error(
        self, test_user, user_tagged_field
    ):
        with patch.object(UserTag.objects, "bulk_create") as mock_bc:
            mock_bc.side_effect = IntegrityError("Duplicate key")

            with pytest.raises(ValidationError, match="Duplicate user tag"):
                populate_user_tags()

    def test_raises_validation_error_on_data_error(self, test_user, user_tagged_field):
        with patch.object(UserTag.objects, "bulk_create") as mock_bc:
            mock_bc.side_effect = DataError("Invalid data")

            with pytest.raises(ValidationError, match="Invalid data type"):
                populate_user_tags()

    def test_raises_validation_error_on_database_error(
        self, test_user, user_tagged_field
    ):
        with patch.object(UserTag.objects, "bulk_create") as mock_bc:
            mock_bc.side_effect = DatabaseError("Connection failed")

            with pytest.raises(ValidationError, match="Database error"):
                populate_user_tags()

    def test_handles_many_users(self, test_user_factory, user_tagged_field):
        """Should create tags for all users via bulk_create."""
        users = [test_user_factory(username=f"batchuser{i}") for i in range(50)]

        populate_user_tags()

        for u in users:
            assert UserTag.objects.filter(
                user=u, tagged_field=user_tagged_field
            ).exists()


# =============================================================================
# update_fields_that_should_be_synchronised
# =============================================================================


@pytest.mark.django_db
class TestUpdateFieldsThatShouldBeSynchronised:
    """Tests for update_fields_that_should_be_synchronised function."""

    def test_creates_default_sync_config(self):
        """Should create default TagMeSynchronise if it doesn't exist."""
        TagMeSynchronise.objects.filter(name="default").delete()

        update_fields_that_should_be_synchronised()

        assert TagMeSynchronise.objects.filter(name="default").exists()

    def test_skips_deleted_models(self, stale_content_type_factory):
        """Should skip ContentTypes whose model_class() returns None."""
        stale_ct = stale_content_type_factory(
            app_label="nonexistent_app", model="deletedmodel"
        )

        TaggedFieldModel.objects.create(
            content=stale_ct,
            model_name="DeletedModel",
            field_name="orphan_field",
            tag_type="user",
        )

        update_fields_that_should_be_synchronised()

        sync = TagMeSynchronise.objects.get(name="default")
        assert "orphan_field" not in sync.synchronise

    def test_handles_no_tagged_field_models(self):
        """Should handle case where no TaggedFieldModels exist."""
        TaggedFieldModel.objects.all().delete()

        update_fields_that_should_be_synchronised()

        sync = TagMeSynchronise.objects.get(name="default")
        assert sync.synchronise == {} or len(sync.synchronise) == 0

    def test_skips_fields_without_synchronise_attr(self, user_tagged_field):
        """Fields without synchronise=True should not appear in sync config."""
        update_fields_that_should_be_synchronised()

        sync = TagMeSynchronise.objects.get(name="default")
        assert "user_tags_field" not in sync.synchronise


# =============================================================================
# Integration
# =============================================================================


@pytest.mark.django_db
class TestTagMgmtSystemIntegration:
    """Integration tests for the complete tag management workflow.

    Each test creates isolated data using unique app_labels/model names
    so they don't interfere with each other or with real registrations.
    """

    def test_full_population_workflow(self, test_user_factory):
        """Both system and user tags should be created in a single run."""
        user1 = test_user_factory(username="intuser1")
        user2 = test_user_factory(username="intuser2")

        ct, _ = ContentType.objects.get_or_create(
            app_label="integration", model="integrationmodel"
        )
        TaggedFieldModel.objects.filter(content=ct).delete()

        user_field = TaggedFieldModel.objects.create(
            content=ct,
            model_name="IntegrationModel",
            field_name="int_user_field",
            tag_type="user",
        )
        system_field = TaggedFieldModel.objects.create(
            content=ct,
            model_name="IntegrationModel",
            field_name="int_system_field",
            tag_type="system",
            default_tags="sys1,sys2,",
        )

        populate_all_tag_records()

        # SystemTag created with correct tags
        system_tag = SystemTag.objects.get(tagged_field=system_field)
        assert system_tag.tags == "sys1,sys2,"

        # Both users have UserTags for the user field
        assert UserTag.objects.filter(user=user1, tagged_field=user_field).exists()
        assert UserTag.objects.filter(user=user2, tagged_field=user_field).exists()

        # No UserTags for system field
        assert not UserTag.objects.filter(tagged_field=system_field).exists()

    def test_incremental_population(self, test_user_factory):
        """New users and fields should be populated incrementally."""
        ct, _ = ContentType.objects.get_or_create(
            app_label="incremental", model="incrementalmodel"
        )
        TaggedFieldModel.objects.filter(content=ct).delete()

        user1 = test_user_factory(username="incuser1")
        field1 = TaggedFieldModel.objects.create(
            content=ct,
            model_name="IncrementalModel",
            field_name="inc_field1",
            tag_type="user",
        )

        # Initial population
        populate_user_tags(user=user1)
        assert UserTag.objects.filter(user=user1, tagged_field=field1).count() == 1

        # Add new user + new field
        user2 = test_user_factory(username="incuser2")
        field2 = TaggedFieldModel.objects.create(
            content=ct,
            model_name="IncrementalModel",
            field_name="inc_field2",
            tag_type="user",
        )

        # Populate user1 → should pick up field2
        populate_user_tags(user=user1)
        assert UserTag.objects.filter(user=user1, tagged_field=field2).exists()

        # Populate user2 → should pick up both fields
        populate_user_tags(user=user2)
        assert UserTag.objects.filter(user=user2, tagged_field=field1).exists()
        assert UserTag.objects.filter(user=user2, tagged_field=field2).exists()

        # Total: 4 combinations
        total = UserTag.objects.filter(
            user__in=[user1, user2], tagged_field__in=[field1, field2]
        ).count()
        assert total == 4
