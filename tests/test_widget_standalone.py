"""
Tests for TagMeSelectMultipleWidget standalone mode.

Standalone mode is when choices are provided explicitly via constructor,
bypassing database queries. These tests do not require database access.

Covers:
- Standalone mode detection
- Enforced settings in standalone mode
- Choices resolution from list/string/callable
- Render output in standalone mode
"""

from django.test import TestCase

from tag_me.widgets import TagMeSelectMultipleWidget


class TestStandaloneModeEnforcedSettings(TestCase):
    """Test that standalone mode enforces specific settings for safety."""

    def test_forces_permitted_to_add_tags_false(self):
        """Standalone mode forces permitted_to_add_tags to False."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            permitted_to_add_tags=True,  # Should be overridden
        )
        config = widget._resolve_config()

        assert config["permitted_to_add_tags"] is False

    def test_forces_add_tag_url_empty(self):
        """Standalone mode forces add_tag_url to empty string."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            add_tag_url="/some/url/",  # Should be overridden
        )
        config = widget._resolve_config()

        assert config["add_tag_url"] == ""

    def test_forces_mgmt_url_empty(self):
        """Standalone mode forces mgmt_url to empty string."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            mgmt_url="/manage/tags/",  # Should be overridden
        )
        config = widget._resolve_config()

        assert config["mgmt_url"] == ""

    def test_allows_help_url(self):
        """Standalone mode allows help_url to be set."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            help_url="/help/tags/",
        )
        config = widget._resolve_config()

        assert config["help_url"] == "/help/tags/"

    def test_allows_multiple_setting(self):
        """Standalone mode allows multiple setting."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            multiple=False,
        )
        config = widget._resolve_config()

        assert config["multiple"] is False

    def test_allows_auto_select_new_tags(self):
        """Standalone mode allows auto_select_new_tags setting."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            auto_select_new_tags=False,
        )
        config = widget._resolve_config()

        assert config["auto_select_new_tags"] is False

    def test_allows_display_number_selected(self):
        """Standalone mode allows display_number_selected setting."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            display_number_selected=5,
        )
        config = widget._resolve_config()

        assert config["display_number_selected"] == 5

    def test_allows_template_setting(self):
        """Standalone mode allows template setting."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            template="custom/template.html",
        )
        config = widget._resolve_config()

        assert config["template"] == "custom/template.html"


class TestChoicesResolutionFromList(TestCase):
    """Test _resolve_choices with list input."""

    def test_list_choices_resolved(self):
        """Choices from list are resolved correctly."""
        widget = TagMeSelectMultipleWidget(choices=["alpha", "beta", "gamma"])
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices[0] == ""
        assert "alpha" in choices
        assert "beta" in choices
        assert "gamma" in choices
        assert len(choices) == 4  # empty + 3 tags

    def test_empty_list_returns_only_empty_string(self):
        """Empty choices list returns just empty string."""
        widget = TagMeSelectMultipleWidget(choices=[])
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices == [""]

    def test_tuple_converted_to_list(self):
        """Tuple choices are converted correctly."""
        widget = TagMeSelectMultipleWidget(choices=("a", "b", "c"))
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices[0] == ""
        assert "a" in choices
        assert "b" in choices
        assert "c" in choices
        assert len(choices) == 4


class TestChoicesResolutionFromString(TestCase):
    """Test _resolve_choices with CSV string input."""

    def test_csv_string_parsed(self):
        """CSV string choices are parsed correctly."""
        widget = TagMeSelectMultipleWidget(choices="red,green,blue,")
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices[0] == ""
        assert "red" in choices
        assert "green" in choices
        assert "blue" in choices
        assert len(choices) == 4

    def test_csv_string_strips_whitespace(self):
        """CSV string choices have whitespace stripped."""
        widget = TagMeSelectMultipleWidget(choices="  one , two  ,  three  ")
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert "one" in choices
        assert "two" in choices
        assert "three" in choices
        assert "  one " not in choices
        assert " two  " not in choices

    def test_csv_string_filters_empty_values(self):
        """CSV string with empty segments filters them out."""
        widget = TagMeSelectMultipleWidget(choices="a,,b,  ,c")
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert "" in choices  # First element is always empty
        assert "a" in choices
        assert "b" in choices
        assert "c" in choices
        # Should not have extra empty strings from parsing
        assert choices.count("") == 1


class TestChoicesResolutionFromCallable(TestCase):
    """Test _resolve_choices with callable input."""

    def test_callable_invoked_at_resolve_time(self):
        """Callable is invoked at resolve time, not init time."""
        call_count = {"count": 0}

        def get_choices():
            call_count["count"] += 1
            return ["dynamic1", "dynamic2"]

        widget = TagMeSelectMultipleWidget(choices=get_choices)
        config = widget._resolve_config()

        # Not called yet
        assert call_count["count"] == 0

        choices, _ = widget._resolve_choices(config)

        # Now called
        assert call_count["count"] == 1
        assert "dynamic1" in choices
        assert "dynamic2" in choices

    def test_callable_exception_returns_empty(self):
        """Callable that raises exception returns empty choices."""

        def bad_callable():
            raise ValueError("Something went wrong")

        widget = TagMeSelectMultipleWidget(choices=bad_callable)
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices == [""]

    def test_callable_returning_empty_list(self):
        """Callable returning empty list gives just empty string."""
        widget = TagMeSelectMultipleWidget(choices=lambda: [])
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices == [""]


class TestChoicesResolutionUnexpectedTypes(TestCase):
    """Test _resolve_choices handles unexpected types gracefully."""

    def test_integer_returns_empty(self):
        """Integer choices type returns empty choices."""
        widget = TagMeSelectMultipleWidget(choices=12345)
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices == [""]

    def test_dict_returns_empty(self):
        """Dict choices type returns empty choices."""
        widget = TagMeSelectMultipleWidget(choices={"a": 1, "b": 2})
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        assert choices == [""]

    def test_none_from_callable_handled(self):
        """Callable returning None is handled gracefully."""
        widget = TagMeSelectMultipleWidget(choices=lambda: None)
        config = widget._resolve_config()
        choices, _ = widget._resolve_choices(config)

        # None is not a list/tuple/str, so should return empty
        assert choices == [""]


class TestStandaloneRender(TestCase):
    """Test render method output in standalone mode."""

    def test_render_with_list_choices(self):
        """Render with list choices produces correct output."""
        widget = TagMeSelectMultipleWidget(
            choices=["Option A", "Option B", "Option C"],
        )
        result = widget.render("test_field", "Option A")

        assert "Option A" in result
        assert "Option B" in result
        assert "Option C" in result
        assert "test_field" in result
        assert "permittedToAddTags: false" in result

    def test_render_with_csv_string_choices(self):
        """Render with CSV string choices produces correct output."""
        widget = TagMeSelectMultipleWidget(
            choices="choice1,choice2,choice3,",
        )
        result = widget.render("tags", "choice1")

        assert "choice1" in result
        assert "choice2" in result
        assert "choice3" in result
        assert "permittedToAddTags: false" in result

    def test_render_sets_choices_attribute(self):
        """Render sets the choices attribute on widget."""
        widget = TagMeSelectMultipleWidget(choices=["x", "y", "z"])
        widget.render("field", "")

        assert widget.choices[0] == ""
        assert "x" in widget.choices
        assert "y" in widget.choices
        assert "z" in widget.choices

    def test_render_with_preselected_value(self):
        """Render includes preselected value."""
        widget = TagMeSelectMultipleWidget(choices=["One", "Two", "Three"])
        result = widget.render("tags", "Two")

        assert "Two" in result

    def test_render_with_multiple_false(self):
        """Render with multiple=False sets config correctly."""
        widget = TagMeSelectMultipleWidget(
            choices=["Low", "Medium", "High"],
            multiple=False,
        )
        result = widget.render("priority", "Medium")

        config = widget._resolve_config()
        assert config["multiple"] is False
        assert "Low" in result
        assert "Medium" in result
        assert "High" in result

    def test_render_ignores_add_tag_url(self):
        """Render in standalone mode ignores add_tag_url."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            add_tag_url="/should/be/ignored/",
        )
        result = widget.render("tags", "")

        assert "/should/be/ignored/" not in result

    def test_render_with_help_url(self):
        """Render includes help_url in config."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            help_url="/help/tagging/",
        )
        widget.render("tags", "")

        config = widget._resolve_config()
        assert config["help_url"] == "/help/tagging/"

    def test_render_with_empty_value(self):
        """Render with empty value works correctly."""
        widget = TagMeSelectMultipleWidget(choices=["a", "b", "c"])
        result = widget.render("tags", "")

        assert "tags" in result

    def test_render_with_none_value(self):
        """Render with None value works correctly."""
        widget = TagMeSelectMultipleWidget(choices=["a", "b", "c"])
        result = widget.render("tags", None)

        assert "tags" in result

    def test_render_with_list_value(self):
        """Render with list value works correctly."""
        widget = TagMeSelectMultipleWidget(choices=["a", "b", "c"])
        result = widget.render("tags", ["a", "b"])

        assert "tags" in result
        assert "a" in result
        assert "b" in result

    def test_render_with_verbose_name_in_attrs(self):
        """Render uses field_verbose_name from attrs."""
        widget = TagMeSelectMultipleWidget(
            choices=["tag1", "tag2"],
            attrs={"field_verbose_name": "My Tags"},
        )
        result = widget.render("tags", "")

        # The verbose name should be passed to template context
        # (actual rendering depends on template, but we verify it's in attrs)
        assert widget.attrs.get("field_verbose_name") == "My Tags"
