"""
Tests for tag_me/utils/tag_mgmt_system.py

This test module provides comprehensive coverage for the tag management system utilities,
including:
- populate_all_tag_records() orchestrator
- _populate_system_tags()
- _populate_user_tags()
- update_fields_that_should_be_synchronised()

Run with: pytest tests/test_tag_mgmt_system.py -v
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import DatabaseError, DataError, IntegrityError
from django.test import TransactionTestCase

from tag_me.models import (
    SystemTag,
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tag_me.utils.tag_mgmt_system import (
    _populate_system_tags,
    _populate_user_tags,
    populate_all_tag_records,
    update_fields_that_should_be_synchronised,
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def second_user(db):
    """Create a second test user."""
    return User.objects.create_user(username="testuser2", password="testpass2")


@pytest.fixture
def content_type(db):
    """Get or create a ContentType for testing."""
    ct, _ = ContentType.objects.get_or_create(
        app_label="tests",
        model="tagmgmttestmodel",
    )
    return ct


@pytest.fixture
def user_tagged_field(db, content_type):
    """Create a user-type TaggedFieldModel."""
    return TaggedFieldModel.objects.create(
        content=content_type,
        model_name="TagMgmtTestModel",
        model_verbose_name="Tag Mgmt Test Model",
        field_name="user_tags_field",
        field_verbose_name="User Tags Field",
        tag_type="user",
        default_tags="",
    )


@pytest.fixture
def system_tagged_field(db, content_type):
    """Create a system-type TaggedFieldModel with default tags."""
    return TaggedFieldModel.objects.create(
        content=content_type,
        model_name="TagMgmtTestModel",
        model_verbose_name="Tag Mgmt Test Model",
        field_name="system_tags_field",
        field_verbose_name="System Tags Field",
        tag_type="system",
        default_tags="option1,option2,option3,",
    )


@pytest.fixture
def system_tagged_field_no_defaults(db, content_type):
    """Create a system-type TaggedFieldModel without default tags."""
    return TaggedFieldModel.objects.create(
        content=content_type,
        model_name="TagMgmtTestModel",
        model_verbose_name="Tag Mgmt Test Model",
        field_name="system_tags_empty",
        field_verbose_name="System Tags Empty",
        tag_type="system",
        default_tags="",  # No defaults
    )


# =============================================================================
# POPULATE_ALL_TAG_RECORDS TESTS
# =============================================================================


class TestPopulateAllTagRecords:
    """Tests for the main orchestrator function."""

    @pytest.mark.django_db
    def test_populate_all_calls_system_and_user(
        self, user, user_tagged_field, system_tagged_field
    ):
        """populate_all_tag_records should call both system and user population."""
        # Run the orchestrator
        populate_all_tag_records()

        # Should have created a SystemTag for the system field
        assert SystemTag.objects.filter(tagged_field=system_tagged_field).exists()

        # Should have created a UserTag for each user/field combination
        assert UserTag.objects.filter(
            user=user, tagged_field=user_tagged_field
        ).exists()

    @pytest.mark.django_db
    def test_populate_all_for_specific_user(self, user, second_user, user_tagged_field):
        """populate_all_tag_records with user arg should only populate that user."""
        # Run for specific user only
        populate_all_tag_records(user=user)

        # Should have UserTag for specified user
        assert UserTag.objects.filter(
            user=user, tagged_field=user_tagged_field
        ).exists()

        # Should NOT have UserTag for other user
        assert not UserTag.objects.filter(
            user=second_user, tagged_field=user_tagged_field
        ).exists()

    @pytest.mark.django_db
    def test_populate_all_handles_exception(self, user_tagged_field):
        """populate_all_tag_records should re-raise exceptions after logging."""
        with patch("tag_me.utils.tag_mgmt_system._populate_system_tags") as mock_sys:
            mock_sys.side_effect = ValidationError("Test error")

            with pytest.raises(ValidationError, match="Test error"):
                populate_all_tag_records()

    @pytest.mark.django_db
    def test_populate_all_idempotent(
        self, user, user_tagged_field, system_tagged_field
    ):
        """Running populate_all_tag_records twice should not create duplicates."""
        populate_all_tag_records()

        user_tag_count = UserTag.objects.count()
        system_tag_count = SystemTag.objects.count()

        # Run again
        populate_all_tag_records()

        # Counts should be the same
        assert UserTag.objects.count() == user_tag_count
        assert SystemTag.objects.count() == system_tag_count


# =============================================================================
# _POPULATE_SYSTEM_TAGS TESTS
# =============================================================================


class TestPopulateSystemTags:
    """Tests for _populate_system_tags function."""

    @pytest.mark.django_db
    def test_creates_system_tag_for_system_field(self, system_tagged_field):
        """Should create SystemTag for fields with tag_type='system'."""
        _populate_system_tags()

        system_tag = SystemTag.objects.get(tagged_field=system_tagged_field)
        assert system_tag.tags == system_tagged_field.default_tags
        assert system_tag.field_name == system_tagged_field.field_name
        assert system_tag.model_name == system_tagged_field.model_name

    @pytest.mark.django_db
    def test_skips_system_field_without_default_tags(
        self, system_tagged_field_no_defaults
    ):
        """Should skip system fields that have no default_tags."""
        _populate_system_tags()

        # Should not create SystemTag for field with empty default_tags
        assert not SystemTag.objects.filter(
            tagged_field=system_tagged_field_no_defaults
        ).exists()

    @pytest.mark.django_db
    def test_updates_existing_system_tag(self, system_tagged_field):
        """Should update existing SystemTag if tags change."""
        # Create initial
        _populate_system_tags()

        original_tag = SystemTag.objects.get(tagged_field=system_tagged_field)
        original_id = original_tag.id

        # Update the TaggedFieldModel
        system_tagged_field.default_tags = "new1,new2,new3,"
        system_tagged_field.save()

        # Run again
        _populate_system_tags()

        # Should have updated, not created new
        updated_tag = SystemTag.objects.get(tagged_field=system_tagged_field)
        assert updated_tag.id == original_id
        assert updated_tag.tags == "new1,new2,new3,"

    @pytest.mark.django_db
    def test_no_system_fields_logs_message(self, user_tagged_field):
        """Should handle case where no system fields exist."""
        # Only user field exists, no system fields
        # This should not raise, just log and return
        _populate_system_tags()

        assert SystemTag.objects.count() == 0

    @pytest.mark.django_db
    def test_handles_integrity_error(self, system_tagged_field):
        """Should raise ValidationError on IntegrityError."""
        with patch.object(SystemTag.objects, "update_or_create") as mock_uoc:
            mock_uoc.side_effect = IntegrityError("Duplicate key")

            with pytest.raises(ValidationError, match="Duplicate system tag"):
                _populate_system_tags()

    @pytest.mark.django_db
    def test_handles_data_error(self, system_tagged_field):
        """Should raise ValidationError on DataError."""
        with patch.object(SystemTag.objects, "update_or_create") as mock_uoc:
            mock_uoc.side_effect = DataError("Invalid data")

            with pytest.raises(ValidationError, match="Invalid data type"):
                _populate_system_tags()

    @pytest.mark.django_db
    def test_handles_database_error(self, system_tagged_field):
        """Should raise ValidationError on DatabaseError."""
        with patch.object(SystemTag.objects, "update_or_create") as mock_uoc:
            mock_uoc.side_effect = DatabaseError("Connection failed")

            with pytest.raises(ValidationError, match="Database error"):
                _populate_system_tags()


# =============================================================================
# _POPULATE_USER_TAGS TESTS
# =============================================================================


class TestPopulateUserTags:
    """Tests for _populate_user_tags function."""

    @pytest.mark.django_db
    def test_creates_user_tag_for_each_user_field_combo(
        self, user, second_user, user_tagged_field
    ):
        """Should create UserTag for each user/field combination."""
        _populate_user_tags()

        # Both users should have a tag for the field
        assert UserTag.objects.filter(
            user=user, tagged_field=user_tagged_field
        ).exists()
        assert UserTag.objects.filter(
            user=second_user, tagged_field=user_tagged_field
        ).exists()

    @pytest.mark.django_db
    def test_specific_user_only_creates_for_that_user(
        self, user, second_user, user_tagged_field
    ):
        """Should only create for specific user when provided."""
        _populate_user_tags(user=user)

        assert UserTag.objects.filter(
            user=user, tagged_field=user_tagged_field
        ).exists()
        assert not UserTag.objects.filter(
            user=second_user, tagged_field=user_tagged_field
        ).exists()

    @pytest.mark.django_db
    def test_skips_existing_combinations(self, user, user_tagged_field):
        """Should skip user/field combinations that already exist."""
        # Pre-create a UserTag
        existing = UserTag.objects.create(
            user=user,
            tagged_field=user_tagged_field,
            model_name="TagMgmtTestModel",
            field_name="user_tags_field",
            tags="existing_tag,",
        )

        _populate_user_tags()

        # Should not have modified the existing tag
        existing.refresh_from_db()
        assert existing.tags == "existing_tag,"

        # Should still be only one UserTag for this combo
        assert (
            UserTag.objects.filter(user=user, tagged_field=user_tagged_field).count()
            == 1
        )

    @pytest.mark.django_db
    def test_creates_new_field_for_existing_users(self, db):
        """Should create UserTags for new fields even if user has other tags."""
        # Create fresh user and content type for isolation
        test_user = User.objects.create_user(username="newfielduser", password="pass")
        ct, _ = ContentType.objects.get_or_create(
            app_label="tests",
            model="newfieldtestmodel",
        )

        # Create first field
        field1 = TaggedFieldModel.objects.create(
            content=ct,
            model_name="NewFieldTestModel",
            field_name="existing_field",
            field_verbose_name="Existing Field",
            tag_type="user",
        )

        # Pre-create a UserTag for first field
        UserTag.objects.create(
            user=test_user,
            tagged_field=field1,
            model_name="NewFieldTestModel",
            field_name="existing_field",
            tags="existing,",
        )

        # Create a NEW field
        field2 = TaggedFieldModel.objects.create(
            content=ct,
            model_name="NewFieldTestModel",
            field_name="new_field",
            field_verbose_name="New Field",
            tag_type="user",
        )

        # Populate for this specific user
        _populate_user_tags(user=test_user)

        # Should have created UserTag for new field
        assert UserTag.objects.filter(user=test_user, tagged_field=field2).exists()

        # Original tag should still exist unchanged
        original = UserTag.objects.get(user=test_user, tagged_field=field1)
        assert original.tags == "existing,"

    @pytest.mark.django_db
    def test_no_user_fields_logs_message(self, user, system_tagged_field):
        """Should handle case where no user fields exist."""
        # Only system field exists
        _populate_user_tags()

        # Should not create any UserTags (system fields are excluded)
        assert UserTag.objects.count() == 0

    @pytest.mark.django_db
    def test_no_users_creates_nothing(self, user_tagged_field):
        """Should handle case where no users exist."""
        # Delete all users
        User.objects.all().delete()

        _populate_user_tags()

        assert UserTag.objects.count() == 0

    @pytest.mark.django_db
    def test_handles_integrity_error(self, user, user_tagged_field):
        """Should raise ValidationError on IntegrityError."""
        with patch.object(UserTag.objects, "bulk_create") as mock_bc:
            mock_bc.side_effect = IntegrityError("Duplicate key")

            with pytest.raises(ValidationError, match="Duplicate user tag"):
                _populate_user_tags()

    @pytest.mark.django_db
    def test_handles_data_error(self, user, user_tagged_field):
        """Should raise ValidationError on DataError."""
        with patch.object(UserTag.objects, "bulk_create") as mock_bc:
            mock_bc.side_effect = DataError("Invalid data")

            with pytest.raises(ValidationError, match="Invalid data type"):
                _populate_user_tags()

    @pytest.mark.django_db
    def test_handles_database_error(self, user, user_tagged_field):
        """Should raise ValidationError on DatabaseError."""
        with patch.object(UserTag.objects, "bulk_create") as mock_bc:
            mock_bc.side_effect = DatabaseError("Connection failed")

            with pytest.raises(ValidationError, match="Database error"):
                _populate_user_tags()

    @pytest.mark.django_db
    def test_batching_with_many_users(self, user_tagged_field):
        """Should batch creation when many users exist."""
        # Create 50 users (less than batch size but enough to test)
        users = [
            User.objects.create_user(username=f"batchuser{i}", password="pass")
            for i in range(50)
        ]

        _populate_user_tags()

        # All users should have UserTags
        for u in users:
            assert UserTag.objects.filter(
                user=u, tagged_field=user_tagged_field
            ).exists()


# =============================================================================
# UPDATE_FIELDS_THAT_SHOULD_BE_SYNCHRONISED TESTS
# =============================================================================


class TestUpdateFieldsThatShouldBeSynchronised:
    """Tests for update_fields_that_should_be_synchronised function."""

    @pytest.mark.django_db
    def test_creates_default_sync_config(self):
        """Should create default TagMeSynchronise if it doesn't exist."""
        # Ensure none exists
        TagMeSynchronise.objects.all().delete()

        update_fields_that_should_be_synchronised()

        assert TagMeSynchronise.objects.filter(name="default").exists()

    @pytest.mark.django_db
    def test_skips_deleted_models(self):
        """Should skip ContentTypes whose model no longer exists."""
        # Create a TaggedFieldModel pointing to a fake/deleted model
        fake_ct, _ = ContentType.objects.get_or_create(
            app_label="nonexistent_app",
            model="deletedmodel",
        )

        TaggedFieldModel.objects.create(
            content=fake_ct,
            model_name="DeletedModel",
            field_name="orphan_field",
            tag_type="user",
        )

        # Should not raise - should skip the missing model
        update_fields_that_should_be_synchronised()

        # Sync should exist but field should not be in it
        # (since model_class() returns None for nonexistent models)
        sync = TagMeSynchronise.objects.get(name="default")
        assert "orphan_field" not in sync.synchronise

    @pytest.mark.django_db
    def test_handles_empty_tagged_field_models(self):
        """Should handle case where no TaggedFieldModels exist."""
        TaggedFieldModel.objects.all().delete()

        # Should not raise
        update_fields_that_should_be_synchronised()

        sync = TagMeSynchronise.objects.get(name="default")
        assert sync.synchronise == {} or len(sync.synchronise) == 0

    @pytest.mark.django_db
    def test_skips_fields_without_synchronise_attr(self, user_tagged_field):
        """Should skip fields that don't have synchronise=True."""
        # The user_tagged_field fixture creates a TaggedFieldModel
        # The actual model field it references may or may not have synchronise
        # This test verifies the function runs without error

        update_fields_that_should_be_synchronised()

        # The function should complete without error
        sync = TagMeSynchronise.objects.get(name="default")
        # user_tags_field from fixture shouldn't be in sync (no synchronise attr)
        assert "user_tags_field" not in sync.synchronise


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestTagMgmtSystemIntegration(TransactionTestCase):
    """Integration tests for the complete tag management workflow."""

    def test_full_population_workflow(self):
        """Test the complete tag population workflow."""
        # Clean slate for this test
        User.objects.filter(username__startswith="intuser").delete()

        # Create users
        user1 = User.objects.create_user(username="intuser1", password="pass")
        user2 = User.objects.create_user(username="intuser2", password="pass")

        # Create content type
        ct, _ = ContentType.objects.get_or_create(
            app_label="integration",
            model="integrationmodel",
        )

        # Clean any existing tagged fields for this content type
        TaggedFieldModel.objects.filter(content=ct).delete()

        # Create both types of fields
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

        # Run full population
        populate_all_tag_records()

        # Verify SystemTag created
        assert SystemTag.objects.filter(tagged_field=system_field).exists()
        system_tag = SystemTag.objects.get(tagged_field=system_field)
        assert system_tag.tags == "sys1,sys2,"

        # Verify UserTags created for both users
        assert UserTag.objects.filter(user=user1, tagged_field=user_field).exists()
        assert UserTag.objects.filter(user=user2, tagged_field=user_field).exists()

        # Verify UserTags NOT created for system field
        assert not UserTag.objects.filter(tagged_field=system_field).exists()

    def test_incremental_population(self):
        """Test that new users/fields get populated incrementally."""
        # Create isolated test data with unique identifiers
        ct, _ = ContentType.objects.get_or_create(
            app_label="incremental",
            model="incrementalmodel",
        )

        # Clean only our test data
        User.objects.filter(username__startswith="incuser").delete()
        TaggedFieldModel.objects.filter(content=ct).delete()

        # Setup initial state
        user1 = User.objects.create_user(username="incuser1", password="pass")
        field1 = TaggedFieldModel.objects.create(
            content=ct,
            model_name="IncrementalModel",
            field_name="inc_field1",
            tag_type="user",
        )

        # Initial population for just this user
        _populate_user_tags(user=user1)

        # Should have 1 UserTag: user1 + field1
        assert UserTag.objects.filter(user=user1, tagged_field=field1).count() == 1

        # Add new user
        user2 = User.objects.create_user(username="incuser2", password="pass")

        # Add new field
        field2 = TaggedFieldModel.objects.create(
            content=ct,
            model_name="IncrementalModel",
            field_name="inc_field2",
            tag_type="user",
        )

        # Run population for user1 - should add field2
        _populate_user_tags(user=user1)
        assert UserTag.objects.filter(user=user1, tagged_field=field2).exists()

        # Run population for user2 - should add both fields
        _populate_user_tags(user=user2)
        assert UserTag.objects.filter(user=user2, tagged_field=field1).exists()
        assert UserTag.objects.filter(user=user2, tagged_field=field2).exists()

        # Total should be 4: user1+field1, user1+field2, user2+field1, user2+field2
        total = UserTag.objects.filter(
            user__in=[user1, user2], tagged_field__in=[field1, field2]
        ).count()
        assert total == 4
