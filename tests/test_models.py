"""tag-me model tests"""

import logging
import string

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from tag_me.models import (
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)
from tests.models import TaggedFieldTestModel

User = get_user_model()

logger = logging.getLogger(__name__)


class TestTag(TestCase):
    """Test the Tags ABC"""

    def test_tag_model_default_properties(self):
        model = TaggedFieldTestModel()

        assert model.model_class_verbose_name == "Tagged Field Test Model"
        assert model.model_class_name == "TaggedFieldTestModel"

    def test_tag_slugify(self):
        model = TaggedFieldTestModel()

        tag = "asdf"
        assert tag in model.slugify(tag)

    @given(
        st_name=st.text(
            # alphabet=st.characters(
            #     blacklist_categories=[
            #         "Cs",
            #         "Cc",
            #     ],
            #     # codec="ascii",
            # ),
            alphabet=string.ascii_letters,
            min_size=1,
            max_size=50,
        )
    )
    def test_base_created_no_unicode_ok(
        self,
        st_name,
    ):
        tag = TaggedFieldTestModel.objects.create(
            tags=st_name,
        )

        # Note: We need to do some work on the slugify process first...
        # assert TagBase.slugify(tag.tags) in tag.slug

        assert len(tag.slug) >= 8


# =============================================================================
# TagMeSynchronise.check_field_sync_list_lengths TESTS (lines 265-286)
# =============================================================================


class TestCheckFieldSyncListLengths:
    """Tests for TagMeSynchronise.check_field_sync_list_lengths method."""

    @pytest.mark.django_db
    def test_empty_synchronise_dict_logs_info(self, caplog):
        """Empty synchronise dict should log info message."""
        sync = TagMeSynchronise.objects.create(
            name="test_empty",
            synchronise={},
        )

        with caplog.at_level(logging.INFO):
            sync.check_field_sync_list_lengths()

        assert "no field tags listed that require synchronising" in caplog.text

    @pytest.mark.django_db
    def test_zero_items_logs_warning(self, caplog):
        """Field with zero content IDs should log warning."""
        sync = TagMeSynchronise.objects.create(
            name="test_zero",
            synchronise={"empty_field": []},
        )

        with caplog.at_level(logging.WARNING):
            sync.check_field_sync_list_lengths()

        assert "empty_field" in caplog.text
        assert "no content id's listed" in caplog.text

    @pytest.mark.django_db
    def test_one_item_logs_warning(self, caplog):
        """Field with one content ID should log warning."""
        sync = TagMeSynchronise.objects.create(
            name="test_one",
            synchronise={"lonely_field": [1]},
        )

        with caplog.at_level(logging.WARNING):
            sync.check_field_sync_list_lengths()

        assert "lonely_field" in caplog.text
        assert "only has 1 element" in caplog.text

    @pytest.mark.django_db
    def test_two_items_logs_info(self, caplog):
        """Field with two content IDs should log info (minimum required)."""
        sync = TagMeSynchronise.objects.create(
            name="test_two",
            synchronise={"paired_field": [1, 2]},
        )

        with caplog.at_level(logging.INFO):
            sync.check_field_sync_list_lengths()

        assert "paired_field" in caplog.text
        assert "2 required minumum elements" in caplog.text

    @pytest.mark.django_db
    def test_more_than_two_items_logs_info(self, caplog):
        """Field with more than two content IDs should log info."""
        sync = TagMeSynchronise.objects.create(
            name="test_many",
            synchronise={"multi_field": [1, 2, 3, 4]},
        )

        with caplog.at_level(logging.INFO):
            sync.check_field_sync_list_lengths()

        assert "multi_field" in caplog.text
        assert "more than the 2 required minumum elements" in caplog.text


# =============================================================================
# UserTag.save() synchronization TESTS (lines 698-728)
# =============================================================================


class TestUserTagSaveSynchronization:
    """Tests for UserTag.save() tag synchronization logic."""

    @pytest.fixture
    def sync_setup(self, db):
        """Create a sync configuration with two related models."""
        # Create two content types representing different models
        ct1, _ = ContentType.objects.get_or_create(
            app_label="tests",
            model="syncmodel1",
        )
        ct2, _ = ContentType.objects.get_or_create(
            app_label="tests",
            model="syncmodel2",
        )

        # Create tagged fields for both
        tf1 = TaggedFieldModel.objects.create(
            content=ct1,
            model_name="SyncModel1",
            field_name="shared_tags",
            tag_type="user",
        )
        tf2 = TaggedFieldModel.objects.create(
            content=ct2,
            model_name="SyncModel2",
            field_name="shared_tags",
            tag_type="user",
        )

        # Create sync config linking both content types
        sync, _ = TagMeSynchronise.objects.get_or_create(name="default")
        sync.synchronise = {"shared_tags": [ct1.id, ct2.id]}
        sync.save()

        # Create user
        user = User.objects.create_user(
            username="syncuser",
            password="syncpass123",
        )

        return {
            "ct1": ct1,
            "ct2": ct2,
            "tf1": tf1,
            "tf2": tf2,
            "sync": sync,
            "user": user,
        }

    @pytest.mark.django_db
    def test_save_syncs_tags_to_related_usertag(self, sync_setup):
        """Saving UserTag should sync tags to related UserTag."""
        user = sync_setup["user"]
        tf1 = sync_setup["tf1"]
        tf2 = sync_setup["tf2"]

        # Create UserTags for both fields
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

        # Update tags on ut1
        ut1.tags = "synced,tags,"
        ut1.save()

        # ut2 should now have the synced tags
        ut2.refresh_from_db()
        assert ut2.tags == "synced,tags,"

    @pytest.mark.django_db
    def test_save_with_sync_tags_save_true_skips_sync(self, sync_setup):
        """sync_tags_save=True should skip synchronization (prevents infinite loop)."""
        user = sync_setup["user"]
        tf1 = sync_setup["tf1"]
        tf2 = sync_setup["tf2"]

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

        # Save with sync_tags_save=True - should NOT sync
        ut1.tags = "not_synced,"
        ut1.save(sync_tags_save=True)

        # ut2 should still have original tags
        ut2.refresh_from_db()
        assert ut2.tags == "original,"

    @pytest.mark.django_db
    def test_save_with_no_tagged_field_logs_warning(self, sync_setup, caplog):
        """UserTag without tagged_field FK should log warning and skip sync."""
        user = sync_setup["user"]

        # Create UserTag without tagged_field (orphaned)
        ut = UserTag(
            user=user,
            tagged_field=None,
            model_name="OrphanModel",
            field_name="shared_tags",  # This field is in sync config
            tags="orphan,",
        )

        with caplog.at_level(logging.WARNING):
            ut.save()

        assert "has no tagged_field FK" in caplog.text
        assert "skipping tag synchronization" in caplog.text

    @pytest.mark.django_db
    def test_save_handles_missing_related_usertag(self, sync_setup, caplog):
        """Should handle case where related UserTag doesn't exist."""
        user = sync_setup["user"]
        tf1 = sync_setup["tf1"]
        # tf2 exists but no UserTag for it

        ut1 = UserTag.objects.create(
            user=user,
            tagged_field=tf1,
            model_name="SyncModel1",
            field_name="shared_tags",
            tags="initial,",
        )

        # Save should not crash, should log warning
        with caplog.at_level(logging.WARNING):
            ut1.tags = "updated,"
            ut1.save()

        assert "Could not sync tags" in caplog.text

    @pytest.mark.django_db
    def test_save_handles_missing_tagged_field_model(self, sync_setup, caplog):
        """Should handle case where TaggedFieldModel doesn't exist for content_id."""
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

        # Save should not crash, should log warning
        with caplog.at_level(logging.WARNING):
            ut1.tags = "updated,"
            ut1.save()

        assert "Could not sync tags" in caplog.text

    @pytest.mark.django_db
    def test_save_with_field_not_in_sync_config(self, sync_setup):
        """Field not in sync config should save normally without sync."""
        user = sync_setup["user"]
        ct1 = sync_setup["ct1"]

        # Create field not in sync config
        tf_nonsync = TaggedFieldModel.objects.create(
            content=ct1,
            model_name="SyncModel1",
            field_name="private_tags",  # Not in sync config
            tag_type="user",
        )

        ut = UserTag.objects.create(
            user=user,
            tagged_field=tf_nonsync,
            model_name="SyncModel1",
            field_name="private_tags",
            tags="private,",
        )

        # Should save without issues
        ut.tags = "updated_private,"
        ut.save()

        ut.refresh_from_db()
        assert ut.tags == "updated_private,"
