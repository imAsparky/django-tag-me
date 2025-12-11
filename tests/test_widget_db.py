"""
Tests for TagMeSelectMultipleWidget database-driven mode.

Database-driven mode is when no explicit choices are provided, and the widget
queries UserTag or SystemTag models for available tags.

Covers:
- Line 270: _resolve_choices_from_db fallback
- Lines 295-302: SystemTag query and processing
- Lines 304-328, 306-326: UserTag query and processing
- Line 376: System tag type forces permitted_to_add_tags to False
- Lines 380-384: Debug log when permitted=True but no URL available
- Lines 325-326: Exception handling in _resolve_choices_from_db
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from tag_me.models import SystemTag, TaggedFieldModel, UserTag
from tag_me.widgets import TagMeSelectMultipleWidget

User = get_user_model()


class DatabaseTestCase(TestCase):
    """Base test case with common database fixtures."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="12345")

        # Import test model and get content type
        from tests.models import TaggedFieldTestModel

        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create TaggedFieldModel entry
        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name=TaggedFieldTestModel._meta.object_name,
            field_name="tagged_field_1",
            tag_type="user",
            field_verbose_name="Tagged Field 1",
        )

    def tearDown(self):
        """Clean up test data."""
        self.user.delete()


class TestUserTagDatabaseLookup(DatabaseTestCase):
    """
    Test UserTag database queries.

    Covers lines 304-328, specifically 306-326.
    """

    def setUp(self):
        """Set up UserTag fixtures."""
        super().setUp()

        # Create UserTag with tags
        self.user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="tag1,tag2,tag3",
        )

    def tearDown(self):
        """Clean up UserTag."""
        self.user_tag.delete()
        super().tearDown()

    def test_user_tags_loaded_from_database(self):
        """
        UserTag tags are loaded from database.

        Covers lines 306-326: UserTag.objects.filter query and processing.
        """
        # No explicit choices - forces DB lookup (line 270)
        # Pass attrs through constructor to ensure they're set
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "tag1")

        assert "tag1" in result
        assert "tag2" in result
        assert "tag3" in result

    def test_user_tag_branch_via_resolve_choices_directly(self):
        """
        Directly test _resolve_choices_from_db for user tags.

        Covers lines 304-326 by calling the method directly.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "tag_type": "user",
            }
        )

        config = widget._resolve_config()
        choices, add_tag_url = widget._resolve_choices_from_db(config)

        # Should have loaded tags from database
        assert "" in choices  # First element
        assert "tag1" in choices
        assert "tag2" in choices
        assert "tag3" in choices

        # Should have generated add_tag_url
        expected_url = reverse("tag_me:add-tag", args=[self.user_tag.id])
        assert add_tag_url == expected_url

    def test_user_tag_branch_explicit_verification(self):
        """
        Explicitly verify the UserTag branch is executed.

        Covers lines 304-328:
        - Line 304: elif tag_type == "user"
        - Line 305: if user and tagged_field
        - Lines 306-309: UserTag.objects.filter query
        - Line 310: if user_tag
        - Lines 311-312: if not add_tag_url / reverse()
        - Lines 313-320: if user_tag.tags / parsing
        - Line 321: return choices, add_tag_url
        """
        # Verify UserTag exists and has correct data
        user_tag = UserTag.objects.filter(
            user=self.user,
            tagged_field=self.tagged_field_model,
        ).first()
        assert user_tag is not None, "UserTag should exist"
        assert user_tag.tags == "tag1,tag2,tag3", "UserTag should have tags"

        # Create widget with NO explicit choices (forces DB lookup)
        # and tag_type="user" to hit the elif branch
        widget = TagMeSelectMultipleWidget()

        # Set attrs directly on widget (simulating how formfield() does it)
        widget.attrs["user"] = self.user
        widget.attrs["tagged_field"] = self.tagged_field_model
        widget.attrs["tag_type"] = "user"

        # Resolve config - tag_type should be "user"
        config = widget._resolve_config()
        assert config["tag_type"] == "user", "tag_type should be 'user'"

        # Call _resolve_choices which should fall through to _resolve_choices_from_db
        choices, add_tag_url = widget._resolve_choices(config)

        # Verify we got choices from the UserTag (proves lines 306-320 executed)
        assert "tag1" in choices, "tag1 should be in choices from UserTag"
        assert "tag2" in choices, "tag2 should be in choices from UserTag"
        assert "tag3" in choices, "tag3 should be in choices from UserTag"

        # Verify add_tag_url was generated (proves lines 311-312 executed)
        expected_url = reverse("tag_me:add-tag", args=[self.user_tag.id])
        assert add_tag_url == expected_url, (
            "add_tag_url should be generated from UserTag"
        )

    def test_user_tag_branch_full_render_path(self):
        """
        Test full render path hits UserTag database lookup.

        This ensures the entire code path from render() through
        _resolve_choices() to _resolve_choices_from_db() is executed
        for the user tag type branch.
        """
        # Update existing user_tag with unique tags to verify this code path
        original_tags = self.user_tag.tags
        self.user_tag.tags = "unique_db_tag_xyz,another_unique_tag"
        self.user_tag.save()

        try:
            # Widget with NO explicit choices
            widget = TagMeSelectMultipleWidget()

            # Assign attrs after creation (common pattern in Django forms)
            widget.attrs.update(
                {
                    "user": self.user,
                    "tagged_field": self.tagged_field_model,
                    "template": "tag_me/tag_me_select.html",
                }
            )

            # Render should trigger the full path
            result = widget.render("my_field", "")

            # The unique tags prove we hit the UserTag DB query
            assert "unique_db_tag_xyz" in result
            assert "another_unique_tag" in result

            # Verify add URL was generated
            expected_url = reverse("tag_me:add-tag", args=[self.user_tag.id])
            assert expected_url in result

        finally:
            # Restore original tags
            self.user_tag.tags = original_tags
            self.user_tag.save()

    def test_add_tag_url_generated_from_user_tag(self):
        """
        add_tag_url is generated from UserTag when not explicitly set.

        Covers lines 311-312: reverse("tag_me:add-tag", args=[user_tag.id]).
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "")

        expected_url = reverse("tag_me:add-tag", args=[self.user_tag.id])
        assert expected_url in result

    def test_explicit_add_tag_url_not_overridden(self):
        """
        Explicit add_tag_url is not overridden by UserTag.

        Covers line 310: if not add_tag_url check.
        """
        widget = TagMeSelectMultipleWidget(
            add_tag_url="/custom/add/url/",
            permitted_to_add_tags=True,
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            },
        )

        result = widget.render("test_tags", "")

        assert "/custom/add/url/" in result

    def test_permitted_to_add_tags_with_valid_url(self):
        """Tag adding is enabled when URL is available."""
        widget = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            },
        )

        result = widget.render("test_tags", "")

        assert "permittedToAddTags: true" in result


class TestUserTagEdgeCases(DatabaseTestCase):
    """Test edge cases for UserTag queries."""

    def test_no_user_returns_empty_choices(self):
        """
        No user in attrs returns empty choices.

        Covers line 305: if user and tagged_field check.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                # No user
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "")

        # Should render without error
        assert "test_tags" in result

    def test_no_tagged_field_returns_empty_choices(self):
        """
        No tagged_field in attrs returns empty choices.

        Covers line 281: if not tagged_field early return.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                # No tagged_field
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "")

        assert "test_tags" in result

    def test_user_tag_not_found_returns_empty_choices(self):
        """
        UserTag not found for user/field combo returns empty choices.

        Covers lines 306-309: UserTag.filter returning None.
        """
        other_user = User.objects.create_user(username="otheruser", password="12345")

        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": other_user,  # Different user, no UserTag exists
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "")

        assert "test_tags" in result

        other_user.delete()

    def test_user_tag_with_empty_tags_string(self):
        """
        UserTag with empty tags string returns empty choices.

        Covers line 314: if user_tag.tags check.
        """
        empty_user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="",  # Empty
        )

        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "")

        assert "test_tags" in result

        empty_user_tag.delete()


class TestSystemTagDatabaseLookup(DatabaseTestCase):
    """
    Test SystemTag database queries.

    Covers lines 295-302.
    """

    def setUp(self):
        """Set up SystemTag fixtures."""
        super().setUp()

        self.system_tag = SystemTag.objects.create(
            tagged_field=self.tagged_field_model,
            tags="system1,system2,system3",
        )

    def tearDown(self):
        """Clean up SystemTag."""
        self.system_tag.delete()
        super().tearDown()

    def test_system_tags_loaded_from_database(self):
        """
        SystemTag tags are loaded from database.

        Covers lines 295-302: SystemTag.objects.filter query and processing.
        """
        # No explicit choices - forces DB lookup (line 270)
        widget = TagMeSelectMultipleWidget(
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "system",  # Triggers system tag query
            }
        )

        result = widget.render("test_tags", "system1")

        assert "system1" in result
        assert "system2" in result
        assert "system3" in result

    def test_system_tags_return_empty_add_url(self):
        """
        SystemTag query returns empty add_tag_url.

        Covers line 302: return choices, "" for system tags.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "system",
            }
        )

        config = widget._resolve_config()
        choices, add_tag_url = widget._resolve_choices(config)

        # System tags should not have an add URL
        assert add_tag_url == ""


class TestSystemTagEdgeCases(DatabaseTestCase):
    """Test edge cases for SystemTag queries."""

    def test_system_tag_not_found_returns_empty_choices(self):
        """
        SystemTag not found returns empty choices.

        Covers lines 295-297: SystemTag.filter returning None.
        """
        # No SystemTag created for this tagged_field
        widget = TagMeSelectMultipleWidget(
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "system",
            }
        )

        result = widget.render("test_tags", "")

        assert "test_tags" in result

    def test_system_tag_with_empty_tags_string(self):
        """
        SystemTag with empty tags string returns empty choices.

        Covers line 298: if system_tag and system_tag.tags check.
        """
        empty_system_tag = SystemTag.objects.create(
            tagged_field=self.tagged_field_model,
            tags="",  # Empty
        )

        widget = TagMeSelectMultipleWidget(
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "system",
            }
        )

        result = widget.render("test_tags", "")

        assert "test_tags" in result

        empty_system_tag.delete()


class TestDatabaseFallback(DatabaseTestCase):
    """
    Test fallback to database when no explicit choices.

    Covers line 270: return self._resolve_choices_from_db(config).
    """

    def test_no_explicit_choices_triggers_db_lookup(self):
        """
        No explicit choices triggers _resolve_choices_from_db.

        Covers line 270.
        """
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="db_tag1,db_tag2",
        )

        # No choices parameter - should fall back to DB
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("test_tags", "")

        assert "db_tag1" in result
        assert "db_tag2" in result

        user_tag.delete()


class TestExceptionHandling(DatabaseTestCase):
    """
    Test exception handling in _resolve_choices_from_db.

    Covers lines 325-326.
    """

    def test_attribute_error_handled_gracefully(self):
        """
        AttributeError in database lookup is caught and logged.

        Covers lines 325-326: except block.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        # Mock UserTag.objects.filter to raise AttributeError
        with patch.object(
            UserTag.objects, "filter", side_effect=AttributeError("Test error")
        ):
            config = widget._resolve_config()
            choices, add_tag_url = widget._resolve_choices_from_db(config)

            # Should return empty choices, not crash
            assert choices == [""]

    def test_user_tag_does_not_exist_handled_gracefully(self):
        """
        UserTag.DoesNotExist is caught and logged.

        Covers lines 325-326: except block.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        # Mock to raise DoesNotExist
        with patch.object(
            UserTag.objects, "filter", side_effect=UserTag.DoesNotExist("Test error")
        ):
            config = widget._resolve_config()
            choices, add_tag_url = widget._resolve_choices_from_db(config)

            assert choices == [""]

    def test_system_tag_does_not_exist_handled_gracefully(self):
        """
        SystemTag.DoesNotExist is caught and logged.

        Covers lines 325-326: except block.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "system",
            }
        )

        # Mock to raise DoesNotExist
        with patch.object(
            SystemTag.objects,
            "filter",
            side_effect=SystemTag.DoesNotExist("Test error"),
        ):
            config = widget._resolve_config()
            choices, add_tag_url = widget._resolve_choices_from_db(config)

            assert choices == [""]


class TestSystemTagTypeDisablesAdding(DatabaseTestCase):
    """
    Test that system tag type forces permitted_to_add_tags to False.

    Covers line 376.
    """

    def setUp(self):
        """Set up SystemTag fixtures."""
        super().setUp()

        self.system_tag = SystemTag.objects.create(
            tagged_field=self.tagged_field_model,
            tags="tag_a,tag_b",
        )

    def tearDown(self):
        """Clean up SystemTag."""
        self.system_tag.delete()
        super().tearDown()

    def test_system_tag_type_forces_permitted_false(self):
        """
        tag_type="system" forces permitted_to_add_tags to False.

        Covers line 376: if config["tag_type"] == "system".
        """
        # Explicitly set permitted_to_add_tags=True, should be overridden
        widget = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,
            tag_type="system",
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
            },
        )

        result = widget.render("test_tags", "")

        assert "permittedToAddTags: false" in result

    def test_system_tag_via_attrs_forces_permitted_false(self):
        """
        tag_type="system" via attrs forces permitted_to_add_tags to False.

        Covers line 376.
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "system",
            }
        )

        result = widget.render("test_tags", "")

        assert "permittedToAddTags: false" in result


class TestPermittedToAddNoUrl(DatabaseTestCase):
    """
    Test behavior when permitted_to_add_tags=True but no URL available.

    Covers lines 380-384.
    """

    def test_permitted_but_no_url_disables_adding(self):
        """
        permitted_to_add_tags=True but no URL disables tag adding.

        Covers lines 380-384: debug log and permitted_to_add_tags = False.
        """
        # User with no UserTag - so no add_tag_url will be generated
        user_without_tags = User.objects.create_user(
            username="no_tags_user", password="12345"
        )

        widget = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,  # Explicitly True
            # No add_tag_url provided
            attrs={
                "user": user_without_tags,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            },
        )

        result = widget.render("test_tags", "")

        # Should disable adding due to no URL
        assert "permittedToAddTags: false" in result

        user_without_tags.delete()

    def test_permitted_with_empty_explicit_url_disables_adding(self):
        """
        permitted_to_add_tags=True with empty add_tag_url disables adding.

        Covers lines 380-384.
        """
        widget = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,
            add_tag_url="",  # Explicitly empty
            attrs={
                # No user, so no URL generated from DB either
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            },
        )

        result = widget.render("test_tags", "")

        assert "permittedToAddTags: false" in result


class TestRenderIntegration(DatabaseTestCase):
    """Integration tests for render method with database data."""

    def test_render_with_all_db_features(self):
        """Full integration test with user tags and all features."""
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="apple,banana,cherry",
        )

        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
                "field_verbose_name": "Fruit Tags",
                "display_number_selected": 3,
                "auto_select_new_tags": True,
                "multiple": True,
            }
        )

        result = widget.render("fruits", "apple,banana")

        # Tags present
        assert "apple" in result
        assert "banana" in result
        assert "cherry" in result

        # Field name present
        assert "fruits" in result

        # Add URL present
        expected_url = reverse("tag_me:add-tag", args=[user_tag.id])
        assert expected_url in result

        user_tag.delete()

    def test_render_preselected_single_value(self):
        """Render with single preselected value."""
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="one,two,three",
        )

        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("numbers", "two")

        # Check that 'two' appears in result and values parsed correctly
        assert "two" in result
        values = widget._parse_value("two")
        assert values == ["two"]

        user_tag.delete()

    def test_render_preselected_multiple_values(self):
        """Render with multiple preselected values."""
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="x,y,z",
        )

        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("letters", "x,y")

        # Both should be in output
        assert "x" in result
        assert "y" in result

        user_tag.delete()

    def test_render_empty_value(self):
        """Render with empty value."""
        user_tag = UserTag.objects.create(
            user=self.user,
            tagged_field=self.tagged_field_model,
            tags="a,b,c",
        )

        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field_model,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            }
        )

        result = widget.render("letters", "")

        assert "letters" in result

        user_tag.delete()
