"""
Unit tests for TagMeSelectMultipleWidget.

These tests cover pure unit functionality that does not require database access:
- Constructor parameter storage
- _is_standalone property
- _resolve_config priority chain
- _parse_value method
"""

from unittest.mock import patch

from django.test import TestCase, override_settings

from tag_me.widgets import TagMeSelectMultipleWidget


class TestConstructorParameters(TestCase):
    """Test that constructor parameters are stored correctly."""

    def test_all_explicit_parameters_stored(self):
        """All explicit parameters are stored as instance attributes."""
        widget = TagMeSelectMultipleWidget(
            choices=["a", "b"],
            multiple=False,
            permitted_to_add_tags=True,
            auto_select_new_tags=False,
            display_number_selected=5,
            add_tag_url="/add/",
            help_url="/help/",
            mgmt_url="/manage/",
            template="custom/template.html",
            tag_type="system",
        )

        assert widget._explicit_choices == ["a", "b"]
        assert widget._explicit_multiple is False
        assert widget._explicit_permitted_to_add_tags is True
        assert widget._explicit_auto_select_new_tags is False
        assert widget._explicit_display_number_selected == 5
        assert widget._explicit_add_tag_url == "/add/"
        assert widget._explicit_help_url == "/help/"
        assert widget._explicit_mgmt_url == "/manage/"
        assert widget._explicit_template == "custom/template.html"
        assert widget._explicit_tag_type == "system"

    def test_default_values_are_none(self):
        """All explicit parameters default to None when not provided."""
        widget = TagMeSelectMultipleWidget()

        assert widget._explicit_choices is None
        assert widget._explicit_multiple is None
        assert widget._explicit_permitted_to_add_tags is None
        assert widget._explicit_auto_select_new_tags is None
        assert widget._explicit_display_number_selected is None
        assert widget._explicit_add_tag_url is None
        assert widget._explicit_help_url is None
        assert widget._explicit_mgmt_url is None
        assert widget._explicit_template is None
        assert widget._explicit_tag_type is None

    def test_attrs_passed_to_parent(self):
        """attrs parameter is passed to parent SelectMultiple."""
        widget = TagMeSelectMultipleWidget(
            attrs={"class": "my-class", "data-test": "value"},
        )

        assert widget.attrs.get("class") == "my-class"
        assert widget.attrs.get("data-test") == "value"

    def test_empty_constructor(self):
        """Widget can be instantiated with no arguments."""
        widget = TagMeSelectMultipleWidget()

        assert widget is not None

    def test_attrs_only_constructor(self):
        """Widget can be instantiated with only attrs."""
        widget = TagMeSelectMultipleWidget(
            attrs={
                "multiple": True,
                "auto_select_new_tags": False,
                "display_number_selected": 3,
            }
        )

        assert widget.attrs.get("multiple") is True
        assert widget.attrs.get("auto_select_new_tags") is False
        assert widget.attrs.get("display_number_selected") == 3

    def test_attrs_can_be_updated_after_init(self):
        """Widget attrs can be updated after initialization."""
        widget = TagMeSelectMultipleWidget()
        widget.attrs.update(
            {
                "user": "test_user",
                "tagged_field": 123,
            }
        )

        assert widget.attrs.get("user") == "test_user"
        assert widget.attrs.get("tagged_field") == 123


class TestIsStandaloneProperty(TestCase):
    """Test the _is_standalone property detection."""

    def test_standalone_when_choices_is_list(self):
        """Widget is standalone when choices list is provided."""
        widget = TagMeSelectMultipleWidget(choices=["tag1", "tag2"])

        assert widget._is_standalone is True

    def test_standalone_when_choices_is_string(self):
        """Widget is standalone when choices CSV string is provided."""
        widget = TagMeSelectMultipleWidget(choices="tag1,tag2,tag3")

        assert widget._is_standalone is True

    def test_standalone_when_choices_is_callable(self):
        """Widget is standalone when choices callable is provided."""
        widget = TagMeSelectMultipleWidget(choices=lambda: ["tag1", "tag2"])

        assert widget._is_standalone is True

    def test_standalone_when_choices_is_empty_list(self):
        """Widget is standalone even with empty choices list."""
        widget = TagMeSelectMultipleWidget(choices=[])

        assert widget._is_standalone is True

    def test_not_standalone_when_no_choices(self):
        """Widget is NOT standalone when no choices provided."""
        widget = TagMeSelectMultipleWidget()

        assert widget._is_standalone is False

    def test_not_standalone_when_choices_is_none(self):
        """Widget is NOT standalone when choices explicitly None."""
        widget = TagMeSelectMultipleWidget(choices=None)

        assert widget._is_standalone is False


class TestResolveConfigPriorityChain(TestCase):
    """Test _resolve_config priority: explicit > attrs > settings > defaults."""

    def test_explicit_overrides_attrs(self):
        """Explicit parameter takes priority over attrs."""
        widget = TagMeSelectMultipleWidget(
            multiple=False,
            attrs={"multiple": True},
        )
        config = widget._resolve_config()

        assert config["multiple"] is False

    def test_attrs_override_defaults(self):
        """Attrs take priority over defaults."""
        widget = TagMeSelectMultipleWidget(
            attrs={"multiple": False},
        )
        config = widget._resolve_config()

        assert config["multiple"] is False

    def test_default_used_when_nothing_set(self):
        """Default value used when neither explicit nor attrs set."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["multiple"] is True

    def test_default_tag_type_is_user(self):
        """Default tag_type is 'user'."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["tag_type"] == "user"

    def test_explicit_tag_type_overrides_default(self):
        """Explicit tag_type overrides default."""
        widget = TagMeSelectMultipleWidget(tag_type="system")
        config = widget._resolve_config()

        assert config["tag_type"] == "system"

    def test_attrs_tag_type_overrides_default(self):
        """Attrs tag_type overrides default."""
        widget = TagMeSelectMultipleWidget(attrs={"tag_type": "system"})
        config = widget._resolve_config()

        assert config["tag_type"] == "system"

    @override_settings(DJ_TAG_ME_MAX_NUMBER_DISPLAYED=10)
    def test_settings_used_for_display_number_selected(self):
        """Settings value used as default for display_number_selected."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["display_number_selected"] == 10

    def test_explicit_display_number_overrides_settings(self):
        """Explicit display_number_selected overrides settings."""
        widget = TagMeSelectMultipleWidget(display_number_selected=7)
        config = widget._resolve_config()

        assert config["display_number_selected"] == 7

    @override_settings(
        DJ_TAG_ME_URLS={"help_url": "/settings/help/", "mgmt_url": "/settings/mgmt/"}
    )
    def test_settings_used_for_help_url(self):
        """Settings DJ_TAG_ME_URLS used for help_url default."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["help_url"] == "/settings/help/"

    @override_settings(
        DJ_TAG_ME_URLS={"help_url": "/settings/help/", "mgmt_url": "/settings/mgmt/"}
    )
    def test_settings_used_for_mgmt_url(self):
        """Settings DJ_TAG_ME_URLS used for mgmt_url default."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["mgmt_url"] == "/settings/mgmt/"

    @override_settings(DJ_TAG_ME_TEMPLATES={"default": "custom/default_template.html"})
    def test_settings_used_for_template(self):
        """Settings DJ_TAG_ME_TEMPLATES used for template default."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["template"] == "custom/default_template.html"

    def test_explicit_template_overrides_settings(self):
        """Explicit template overrides settings."""
        widget = TagMeSelectMultipleWidget(template="explicit/template.html")
        config = widget._resolve_config()

        assert config["template"] == "explicit/template.html"

    def test_default_permitted_to_add_tags_is_true(self):
        """Default permitted_to_add_tags is True for non-standalone."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["permitted_to_add_tags"] is True

    def test_default_auto_select_new_tags_is_true(self):
        """Default auto_select_new_tags is True."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["auto_select_new_tags"] is True

    def test_default_add_tag_url_is_empty(self):
        """Default add_tag_url is empty string."""
        widget = TagMeSelectMultipleWidget()
        config = widget._resolve_config()

        assert config["add_tag_url"] == ""


class TestParseValue(TestCase):
    """Test _parse_value method with various input types."""

    def test_none_returns_empty_list(self):
        """None value returns empty list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(None) == []

    def test_empty_string_returns_empty_list(self):
        """Empty string returns empty list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value("") == []

    def test_csv_string_parsed_to_list(self):
        """CSV string is parsed into list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value("tag1,tag2,tag3,") == ["tag1", "tag2", "tag3"]

    def test_csv_string_strips_whitespace(self):
        """CSV string values have whitespace stripped."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value("  tag1 , tag2  ,tag3  ,") == [
            "tag1",
            "tag2",
            "tag3",
        ]

    def test_single_value_string(self):
        """Single value string without comma."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value("single") == ["single"]

    def test_list_returned_cleaned(self):
        """List value is returned cleaned."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(["a", "b", "c"]) == ["a", "b", "c"]

    def test_list_with_empty_strings_filtered(self):
        """Empty strings in list are filtered out."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(["a", "", "b", "  ", "c"]) == ["a", "b", "c"]

    def test_list_strips_whitespace(self):
        """List values have whitespace stripped."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(["  a  ", " b ", "c "]) == ["a", "b", "c"]

    def test_tuple_converted_to_list(self):
        """Tuple input is converted to list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(("x", "y", "z")) == ["x", "y", "z"]

    def test_tuple_with_empty_strings_filtered(self):
        """Empty strings in tuple are filtered out."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(("a", "", "b")) == ["a", "b"]

    def test_integer_returns_empty_list(self):
        """Integer value returns empty list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(12345) == []

    def test_dict_returns_empty_list(self):
        """Dict value returns empty list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value({"key": "value"}) == []

    def test_object_returns_empty_list(self):
        """Arbitrary object returns empty list."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value(object()) == []

    def test_list_with_non_string_values_converted(self):
        """Non-string values in list are converted to strings."""
        widget = TagMeSelectMultipleWidget()

        assert widget._parse_value([1, 2, 3]) == ["1", "2", "3"]
