"""
Tests for TagMeSelectMultipleWidget.

Covers:
    Unit (no DB):
    - Constructor: parameter storage, defaults, attrs passthrough
    - _is_standalone: detection for list, string, callable, None
    - _resolve_config: priority chain (explicit > attrs > settings > defaults),
      standalone overrides
    - _parse_value: string, list, tuple, None, unexpected types
    - Standalone choices: list, CSV string, callable, unexpected types
    - Standalone enforced settings: permitted, add/mgmt/help URLs
    - Standalone render: output, preselected values, config
    - Django rendering pipeline: optgroups safety, form.as_div()

    Database:
    - UserTag lookup: tag loading, URL generation
    - SystemTag lookup: tag loading, empty add URL
    - Edge cases: missing user/tagged_field, empty tags
    - Exception handling: AttributeError, DoesNotExist
    - Permissions: system type, no URL fallback
    - Render integration: full path with DB data

Run with: pytest tests/test_widget.py -v
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse

from tag_me.models import SystemTag, UserTag
from tag_me.widgets import TagMeSelectMultipleWidget

User = get_user_model()


# =============================================================================
# Fixtures (DB tests only)
# =============================================================================


@pytest.fixture
def widget_tagged_field(db, tagged_field_factory):
    """A TaggedFieldModel on a fake ContentType to avoid unique constraint collisions."""
    ct, _ = ContentType.objects.get_or_create(app_label="tests", model="widgettestfake")
    return tagged_field_factory(
        content_type=ct,
        field_name="widget_test_field",
        model_name="WidgetTestFake",
        model_verbose_name="Widget Test Fake",
        field_verbose_name="Widget Test Field",
        tag_type="user",
    )


@pytest.fixture
def widget_user_tag(db, test_user, widget_tagged_field):
    """A UserTag linked to the widget test tagged field."""
    ut = UserTag.objects.create(
        user=test_user,
        tagged_field=widget_tagged_field,
        model_name="WidgetTestFake",
        field_name="widget_test_field",
        field_verbose_name="Widget Test Field",
        tags="tag1,tag2,tag3",
    )
    yield ut
    try:
        ut.delete()
    except Exception:
        pass


@pytest.fixture
def widget_system_tag(db, widget_tagged_field):
    """A SystemTag linked to the widget test tagged field."""
    widget_tagged_field.tag_type = "system"
    widget_tagged_field.save()

    st = SystemTag.objects.create(
        tagged_field=widget_tagged_field,
        model_name="WidgetTestFake",
        field_name="widget_test_field",
        tags="sys1,sys2,sys3",
    )
    yield st
    try:
        st.delete()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_widget(**attrs):
    """Shorthand: create a widget with attrs."""
    return TagMeSelectMultipleWidget(attrs=attrs)


def _make_db_widget(user, tagged_field, tag_type="user", **extra_attrs):
    """Shorthand: create a widget configured for DB-driven mode."""
    attrs = {
        "user": user,
        "tagged_field": tagged_field,
        "template": "tag_me/tag_me_select.html",
        "tag_type": tag_type,
        **extra_attrs,
    }
    return TagMeSelectMultipleWidget(attrs=attrs)


# =============================================================================
# Constructor (no DB)
# =============================================================================


class TestConstructorParameters:
    """Test that constructor parameters are stored correctly."""

    def test_all_explicit_parameters_stored(self):
        w = TagMeSelectMultipleWidget(
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

        assert w._explicit_choices == ["a", "b"]
        assert w._explicit_multiple is False
        assert w._explicit_permitted_to_add_tags is True
        assert w._explicit_auto_select_new_tags is False
        assert w._explicit_display_number_selected == 5
        assert w._explicit_add_tag_url == "/add/"
        assert w._explicit_help_url == "/help/"
        assert w._explicit_mgmt_url == "/manage/"
        assert w._explicit_template == "custom/template.html"
        assert w._explicit_tag_type == "system"

    def test_default_values_are_none(self):
        w = TagMeSelectMultipleWidget()

        assert w._explicit_choices is None
        assert w._explicit_multiple is None
        assert w._explicit_permitted_to_add_tags is None
        assert w._explicit_auto_select_new_tags is None
        assert w._explicit_display_number_selected is None
        assert w._explicit_add_tag_url is None
        assert w._explicit_help_url is None
        assert w._explicit_mgmt_url is None
        assert w._explicit_template is None
        assert w._explicit_tag_type is None

    def test_attrs_passed_to_parent(self):
        w = TagMeSelectMultipleWidget(
            attrs={"class": "my-class", "data-test": "value"},
        )

        assert w.attrs.get("class") == "my-class"
        assert w.attrs.get("data-test") == "value"

    def test_empty_constructor(self):
        w = TagMeSelectMultipleWidget()
        assert w is not None

    def test_attrs_only_constructor(self):
        w = TagMeSelectMultipleWidget(
            attrs={"multiple": True, "display_number_selected": 3},
        )

        assert w.attrs.get("multiple") is True
        assert w.attrs.get("display_number_selected") == 3

    def test_attrs_can_be_updated_after_init(self):
        w = TagMeSelectMultipleWidget()
        w.attrs.update({"user": "test_user", "tagged_field": 123})

        assert w.attrs.get("user") == "test_user"
        assert w.attrs.get("tagged_field") == 123


# =============================================================================
# _is_standalone (no DB)
# =============================================================================


class TestIsStandalone:
    """Test _is_standalone property detection."""

    def test_false_when_no_choices(self):
        assert TagMeSelectMultipleWidget()._is_standalone is False

    def test_false_when_choices_is_none(self):
        assert TagMeSelectMultipleWidget(choices=None)._is_standalone is False

    def test_true_when_choices_is_list(self):
        assert TagMeSelectMultipleWidget(choices=["a", "b"])._is_standalone is True

    def test_true_when_choices_is_empty_list(self):
        assert TagMeSelectMultipleWidget(choices=[])._is_standalone is True

    def test_true_when_choices_is_csv_string(self):
        assert TagMeSelectMultipleWidget(choices="a,b,c")._is_standalone is True

    def test_true_when_choices_is_callable(self):
        assert TagMeSelectMultipleWidget(choices=lambda: ["a"])._is_standalone is True


# =============================================================================
# _resolve_config (no DB)
# =============================================================================


class TestResolveConfig:
    """Test _resolve_config priority chain: explicit > attrs > settings > defaults."""

    # --- Defaults ---

    def test_defaults_when_nothing_set(self):
        config = TagMeSelectMultipleWidget()._resolve_config()

        assert config["multiple"] is True
        assert config["permitted_to_add_tags"] is True
        assert config["auto_select_new_tags"] is True
        assert config["tag_type"] == "user"
        assert config["add_tag_url"] == ""
        assert config["template"] == "tag_me/tag_me_select.html"

    # --- Explicit > attrs > defaults ---

    def test_explicit_overrides_attrs(self):
        w = TagMeSelectMultipleWidget(multiple=False, attrs={"multiple": True})
        assert w._resolve_config()["multiple"] is False

    def test_attrs_override_defaults(self):
        w = TagMeSelectMultipleWidget(attrs={"multiple": False, "tag_type": "system"})
        config = w._resolve_config()

        assert config["multiple"] is False
        assert config["tag_type"] == "system"

    def test_explicit_overrides_defaults(self):
        w = TagMeSelectMultipleWidget(
            multiple=False, auto_select_new_tags=False, tag_type="system"
        )
        config = w._resolve_config()

        assert config["multiple"] is False
        assert config["auto_select_new_tags"] is False
        assert config["tag_type"] == "system"

    # --- Settings fallbacks ---

    @override_settings(DJ_TAG_ME_MAX_NUMBER_DISPLAYED=10)
    def test_settings_display_number_selected(self):
        config = TagMeSelectMultipleWidget()._resolve_config()
        assert config["display_number_selected"] == 10

    def test_explicit_display_number_overrides_settings(self):
        w = TagMeSelectMultipleWidget(display_number_selected=7)
        assert w._resolve_config()["display_number_selected"] == 7

    @override_settings(
        DJ_TAG_ME_URLS={"help_url": "/settings/help/", "mgmt_url": "/settings/mgmt/"}
    )
    def test_settings_help_url(self):
        config = TagMeSelectMultipleWidget()._resolve_config()
        assert config["help_url"] == "/settings/help/"

    @override_settings(
        DJ_TAG_ME_URLS={"help_url": "/settings/help/", "mgmt_url": "/settings/mgmt/"}
    )
    def test_settings_mgmt_url(self):
        config = TagMeSelectMultipleWidget()._resolve_config()
        assert config["mgmt_url"] == "/settings/mgmt/"

    @override_settings(DJ_TAG_ME_TEMPLATES={"default": "custom/template.html"})
    def test_settings_template(self):
        config = TagMeSelectMultipleWidget()._resolve_config()
        assert config["template"] == "custom/template.html"

    def test_explicit_template_overrides_settings(self):
        w = TagMeSelectMultipleWidget(template="explicit/template.html")
        assert w._resolve_config()["template"] == "explicit/template.html"

    # --- Standalone overrides ---

    def test_standalone_forces_safe_defaults(self):
        """Standalone disables add/mgmt but allows help."""
        w = TagMeSelectMultipleWidget(
            choices=["tag1"],
            permitted_to_add_tags=True,
            add_tag_url="/custom/add/",
            mgmt_url="/custom/mgmt/",
            help_url="/custom/help/",
        )
        config = w._resolve_config()

        assert config["permitted_to_add_tags"] is False
        assert config["add_tag_url"] == ""
        assert config["mgmt_url"] == ""
        assert config["help_url"] == "/custom/help/"

    def test_standalone_allows_multiple(self):
        w = TagMeSelectMultipleWidget(choices=["a"], multiple=False)
        assert w._resolve_config()["multiple"] is False

    def test_standalone_allows_auto_select(self):
        w = TagMeSelectMultipleWidget(choices=["a"], auto_select_new_tags=False)
        assert w._resolve_config()["auto_select_new_tags"] is False

    def test_standalone_allows_display_number(self):
        w = TagMeSelectMultipleWidget(choices=["a"], display_number_selected=5)
        assert w._resolve_config()["display_number_selected"] == 5

    def test_standalone_allows_template(self):
        w = TagMeSelectMultipleWidget(choices=["a"], template="custom/t.html")
        assert w._resolve_config()["template"] == "custom/t.html"


# =============================================================================
# _parse_value (no DB)
# =============================================================================


class TestParseValue:
    """Test _parse_value: converts field value to list of selected tags."""

    def test_none_returns_empty_list(self):
        assert TagMeSelectMultipleWidget()._parse_value(None) == []

    def test_empty_string_returns_empty_list(self):
        assert TagMeSelectMultipleWidget()._parse_value("") == []

    def test_csv_string_parsed(self):
        assert TagMeSelectMultipleWidget()._parse_value("tag1,tag2,tag3,") == [
            "tag1",
            "tag2",
            "tag3",
        ]

    def test_csv_string_strips_whitespace(self):
        assert TagMeSelectMultipleWidget()._parse_value("  a , b  ,c  ,") == [
            "a",
            "b",
            "c",
        ]

    def test_single_value_string(self):
        assert TagMeSelectMultipleWidget()._parse_value("solo") == ["solo"]

    def test_list_input(self):
        assert TagMeSelectMultipleWidget()._parse_value(["a", "b", "c"]) == [
            "a",
            "b",
            "c",
        ]

    def test_list_strips_whitespace(self):
        assert TagMeSelectMultipleWidget()._parse_value(["  a  ", " b "]) == ["a", "b"]

    def test_list_filters_empty_strings(self):
        assert TagMeSelectMultipleWidget()._parse_value(["a", "", "  ", "b"]) == [
            "a",
            "b",
        ]

    def test_list_converts_non_strings(self):
        assert TagMeSelectMultipleWidget()._parse_value([1, 2, 3]) == ["1", "2", "3"]

    def test_tuple_input(self):
        assert TagMeSelectMultipleWidget()._parse_value(("x", "y")) == ["x", "y"]

    def test_tuple_filters_empty_strings(self):
        assert TagMeSelectMultipleWidget()._parse_value(("a", "", "b")) == ["a", "b"]

    def test_integer_returns_empty_list(self):
        assert TagMeSelectMultipleWidget()._parse_value(12345) == []

    def test_dict_returns_empty_list(self):
        assert TagMeSelectMultipleWidget()._parse_value({"key": "val"}) == []

    def test_object_returns_empty_list(self):
        assert TagMeSelectMultipleWidget()._parse_value(object()) == []


# =============================================================================
# Standalone Choices Resolution (no DB)
# =============================================================================


class TestChoicesFromList:
    """Test _resolve_choices with list/tuple input."""

    def test_list_resolved(self):
        w = TagMeSelectMultipleWidget(choices=["alpha", "beta", "gamma"])
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == ["", "alpha", "beta", "gamma"]

    def test_empty_list_returns_only_empty_string(self):
        w = TagMeSelectMultipleWidget(choices=[])
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == [""]

    def test_tuple_converted(self):
        w = TagMeSelectMultipleWidget(choices=("a", "b", "c"))
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == ["", "a", "b", "c"]


class TestChoicesFromString:
    """Test _resolve_choices with CSV string input."""

    def test_csv_string_parsed(self):
        w = TagMeSelectMultipleWidget(choices="red,green,blue,")
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == ["", "red", "green", "blue"]

    def test_csv_string_strips_whitespace(self):
        w = TagMeSelectMultipleWidget(choices="  one , two  ,  three  ")
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert "one" in choices
        assert "two" in choices
        assert "three" in choices
        assert "  one " not in choices

    def test_csv_string_filters_empty_segments(self):
        w = TagMeSelectMultipleWidget(choices="a,,b,  ,c")
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices.count("") == 1  # Only the leading empty


class TestChoicesFromCallable:
    """Test _resolve_choices with callable input."""

    def test_callable_invoked_at_resolve_time(self):
        call_count = {"n": 0}

        def get_choices():
            call_count["n"] += 1
            return ["dynamic1", "dynamic2"]

        w = TagMeSelectMultipleWidget(choices=get_choices)
        assert call_count["n"] == 0  # Not called at init

        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert call_count["n"] == 1
        assert "dynamic1" in choices
        assert "dynamic2" in choices

    def test_callable_exception_returns_empty(self):
        def bad_callable():
            raise ValueError("Something went wrong")

        w = TagMeSelectMultipleWidget(choices=bad_callable)
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == [""]

    def test_callable_returning_empty_list(self):
        w = TagMeSelectMultipleWidget(choices=lambda: [])
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == [""]


class TestChoicesUnexpectedTypes:
    """Test _resolve_choices with unexpected input types."""

    def test_integer_returns_empty(self):
        w = TagMeSelectMultipleWidget(choices=12345)
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == [""]

    def test_dict_returns_empty(self):
        w = TagMeSelectMultipleWidget(choices={"a": 1})
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == [""]

    def test_callable_returning_none(self):
        w = TagMeSelectMultipleWidget(choices=lambda: None)
        config = w._resolve_config()
        choices, _ = w._resolve_choices(config)

        assert choices == [""]


# =============================================================================
# Standalone Render (no DB)
# =============================================================================


class TestStandaloneRender:
    """Test render method output in standalone mode."""

    def test_render_with_list_choices(self):
        w = TagMeSelectMultipleWidget(choices=["Option A", "Option B", "Option C"])
        result = w.render("test_field", "Option A")

        assert "Option A" in result
        assert "Option B" in result
        assert "Option C" in result
        assert "test_field" in result
        assert "permittedToAddTags: false" in result

    def test_render_with_csv_string_choices(self):
        w = TagMeSelectMultipleWidget(choices="choice1,choice2,choice3,")
        result = w.render("tags", "choice1")

        assert "choice1" in result
        assert "choice2" in result
        assert "choice3" in result

    def test_render_sets_choices_attribute(self):
        w = TagMeSelectMultipleWidget(choices=["x", "y", "z"])
        w.render("field", "")

        assert w.choices[0] == ""
        assert "x" in w.choices
        assert "y" in w.choices

    def test_render_with_preselected_value(self):
        w = TagMeSelectMultipleWidget(choices=["One", "Two", "Three"])
        result = w.render("tags", "Two")

        assert "Two" in result

    def test_render_with_multiple_false(self):
        w = TagMeSelectMultipleWidget(choices=["Low", "Medium", "High"], multiple=False)
        result = w.render("priority", "Medium")

        assert w._resolve_config()["multiple"] is False
        assert "Low" in result
        assert "Medium" in result

    def test_render_ignores_add_tag_url(self):
        w = TagMeSelectMultipleWidget(
            choices=["tag1"], add_tag_url="/should/be/ignored/"
        )
        result = w.render("tags", "")

        assert "/should/be/ignored/" not in result

    def test_render_empty_value(self):
        w = TagMeSelectMultipleWidget(choices=["a", "b"])
        result = w.render("tags", "")

        assert "tags" in result

    def test_render_none_value(self):
        w = TagMeSelectMultipleWidget(choices=["a", "b"])
        result = w.render("tags", None)

        assert "tags" in result

    def test_render_list_value(self):
        w = TagMeSelectMultipleWidget(choices=["a", "b", "c"])
        result = w.render("tags", ["a", "b"])

        assert "a" in result
        assert "b" in result

    def test_render_verbose_name_from_attrs(self):
        w = TagMeSelectMultipleWidget(
            choices=["tag1"], attrs={"field_verbose_name": "My Tags"}
        )
        w.render("tags", "")

        assert w.attrs.get("field_verbose_name") == "My Tags"

    def test_render_help_url_allowed(self):
        w = TagMeSelectMultipleWidget(choices=["tag1"], help_url="/help/tagging/")
        w.render("tags", "")

        assert w._resolve_config()["help_url"] == "/help/tagging/"


# =============================================================================
# Django Rendering Pipeline (no DB)
# =============================================================================


class TestDjangoRenderingPipeline:
    """Test widget integrates safely with Django's form rendering."""

    def test_optgroups_does_not_raise(self):
        """Django's optgroups() expects (value, label) tuples.

        Our widget uses string choices with a custom template, so optgroups
        must not break if called. Regression test for ValueError.
        """
        w = TagMeSelectMultipleWidget(choices=["tag1", "tag2"])
        try:
            list(w.optgroups("test", []))
        except ValueError as e:
            if "not enough values to unpack" in str(e):
                pytest.fail(
                    "Widget choices caused Django's optgroups() to fail. "
                    "Ensure super().render() is not called or self.choices "
                    "is empty before calling it."
                )
            raise

    @patch("tag_me.widgets.get_template")
    def test_render_through_form_as_div(self, mock_get_template):
        """Full Django form rendering pipeline doesn't break."""
        from django import forms

        mock_template = mock_get_template.return_value
        mock_template.render.return_value = "<select>mocked</select>"

        w = TagMeSelectMultipleWidget(choices=["tag1", "tag2"])

        class TestForm(forms.Form):
            tags = forms.CharField(widget=w, required=False)

        form = TestForm()
        html = form.as_div()

        assert "tags" in str(html)


# =============================================================================
# UserTag Database Lookup
# =============================================================================


@pytest.mark.django_db
class TestUserTagLookup:
    """Test DB-driven mode: UserTag query and processing."""

    def test_loads_tags_from_database(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(test_user, widget_tagged_field)
        config = w._resolve_config()
        choices, _ = w._resolve_choices_from_db(config)

        assert "" in choices
        assert "tag1" in choices
        assert "tag2" in choices
        assert "tag3" in choices

    def test_generates_add_tag_url(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(test_user, widget_tagged_field)
        config = w._resolve_config()
        _, add_tag_url = w._resolve_choices_from_db(config)

        expected = reverse("tag_me:add-tag", args=[widget_user_tag.id])
        assert add_tag_url == expected

    def test_explicit_add_url_not_overridden(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = TagMeSelectMultipleWidget(
            add_tag_url="/custom/add/",
            attrs={
                "user": test_user,
                "tagged_field": widget_tagged_field,
                "tag_type": "user",
            },
        )
        config = w._resolve_config()
        _, add_tag_url = w._resolve_choices_from_db(config)

        assert add_tag_url == "/custom/add/"

    def test_render_includes_tags(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("test_field", "tag1")

        assert "tag1" in result
        assert "tag2" in result
        assert "tag3" in result

    def test_permitted_to_add_with_valid_url(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("test_field", "")

        assert "permittedToAddTags: true" in result


# =============================================================================
# SystemTag Database Lookup
# =============================================================================


@pytest.mark.django_db
class TestSystemTagLookup:
    """Test DB-driven mode: SystemTag query and processing."""

    def test_loads_system_tags_from_database(
        self, widget_tagged_field, widget_system_tag
    ):
        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="system",
        )
        config = w._resolve_config()
        choices, add_tag_url = w._resolve_choices(config)

        assert "sys1" in choices
        assert "sys2" in choices
        assert "sys3" in choices
        assert add_tag_url == ""

    def test_render_includes_system_tags(self, widget_tagged_field, widget_system_tag):
        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="system",
        )
        result = w.render("sys_field", "sys1")

        assert "sys1" in result
        assert "sys2" in result
        assert "sys3" in result


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.django_db
class TestLookupEdgeCases:
    """Edge cases for DB lookups: missing data, empty tags."""

    def test_no_user_returns_empty_choices(self, widget_tagged_field):
        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="user",
        )
        result = w.render("test_field", "")

        assert "test_field" in result

    def test_no_tagged_field_returns_empty_choices(self, test_user):
        w = _make_widget(
            user=test_user,
            template="tag_me/tag_me_select.html",
            tag_type="user",
        )
        result = w.render("test_field", "")

        assert "test_field" in result

    def test_user_tag_not_found_for_different_user(
        self, widget_tagged_field, widget_user_tag, test_user_factory
    ):
        other_user = test_user_factory(username="otheruser")
        w = _make_db_widget(other_user, widget_tagged_field)

        config = w._resolve_config()
        choices, _ = w._resolve_choices_from_db(config)

        assert choices == [""]

    def test_user_tag_with_empty_tags(self, test_user, widget_tagged_field):
        UserTag.objects.create(
            user=test_user,
            tagged_field=widget_tagged_field,
            tags="",
        )

        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("test_field", "")

        assert "test_field" in result

    def test_system_tag_not_found(self, widget_tagged_field):
        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="system",
        )
        result = w.render("test_field", "")

        assert "test_field" in result

    def test_system_tag_with_empty_tags(self, widget_tagged_field):
        widget_tagged_field.tag_type = "system"
        widget_tagged_field.save()
        SystemTag.objects.create(
            tagged_field=widget_tagged_field,
            tags="",
        )

        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="system",
        )
        result = w.render("test_field", "")

        assert "test_field" in result


# =============================================================================
# Exception Handling
# =============================================================================


@pytest.mark.django_db
class TestExceptionHandling:
    """Test that DB errors are caught gracefully."""

    def test_attribute_error_returns_empty_choices(
        self, test_user, widget_tagged_field
    ):
        w = _make_db_widget(test_user, widget_tagged_field)

        with patch.object(
            UserTag.objects, "filter", side_effect=AttributeError("test")
        ):
            config = w._resolve_config()
            choices, _ = w._resolve_choices_from_db(config)

            assert choices == [""]

    def test_user_tag_does_not_exist_returns_empty_choices(
        self, test_user, widget_tagged_field
    ):
        w = _make_db_widget(test_user, widget_tagged_field)

        with patch.object(
            UserTag.objects, "filter", side_effect=UserTag.DoesNotExist("test")
        ):
            config = w._resolve_config()
            choices, _ = w._resolve_choices_from_db(config)

            assert choices == [""]

    def test_system_tag_does_not_exist_returns_empty_choices(self, widget_tagged_field):
        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="system",
        )

        with patch.object(
            SystemTag.objects, "filter", side_effect=SystemTag.DoesNotExist("test")
        ):
            config = w._resolve_config()
            choices, _ = w._resolve_choices_from_db(config)

            assert choices == [""]


# =============================================================================
# Permissions
# =============================================================================


@pytest.mark.django_db
class TestPermissions:
    """Test permitted_to_add_tags logic in render."""

    def test_system_type_forces_permitted_false(
        self, widget_tagged_field, widget_system_tag
    ):
        w = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,
            tag_type="system",
            attrs={
                "tagged_field": widget_tagged_field,
                "template": "tag_me/tag_me_select.html",
            },
        )
        result = w.render("test_field", "")

        assert "permittedToAddTags: false" in result

    def test_system_via_attrs_forces_permitted_false(
        self, widget_tagged_field, widget_system_tag
    ):
        w = _make_widget(
            tagged_field=widget_tagged_field,
            template="tag_me/tag_me_select.html",
            tag_type="system",
        )
        result = w.render("test_field", "")

        assert "permittedToAddTags: false" in result

    def test_permitted_but_no_url_disables_adding(
        self, test_user_factory, widget_tagged_field
    ):
        user_without_tags = test_user_factory(username="notagsuser")

        w = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,
            attrs={
                "user": user_without_tags,
                "tagged_field": widget_tagged_field,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            },
        )
        result = w.render("test_field", "")

        assert "permittedToAddTags: false" in result

    def test_permitted_with_empty_explicit_url_disables_adding(
        self, widget_tagged_field
    ):
        w = TagMeSelectMultipleWidget(
            permitted_to_add_tags=True,
            add_tag_url="",
            attrs={
                "tagged_field": widget_tagged_field,
                "template": "tag_me/tag_me_select.html",
                "tag_type": "user",
            },
        )
        result = w.render("test_field", "")

        assert "permittedToAddTags: false" in result


# =============================================================================
# Render Integration
# =============================================================================


@pytest.mark.django_db
class TestRenderIntegration:
    """Full render path with DB data."""

    def test_render_with_all_features(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(
            test_user,
            widget_tagged_field,
            field_verbose_name="Widget Tags",
            display_number_selected=3,
        )
        result = w.render("widget_field", "tag1,tag2")

        assert "tag1" in result
        assert "tag2" in result
        assert "tag3" in result
        assert "widget_field" in result

        expected_url = reverse("tag_me:add-tag", args=[widget_user_tag.id])
        assert expected_url in result

    def test_render_preselected_single_value(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("field", "tag2")

        assert "tag2" in result

    def test_render_preselected_multiple_values(
        self, test_user, widget_tagged_field, widget_user_tag
    ):
        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("field", "tag1,tag3")

        assert "tag1" in result
        assert "tag3" in result

    def test_render_empty_value(self, test_user, widget_tagged_field, widget_user_tag):
        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("field", "")

        assert "field" in result

    def test_render_none_value(self, test_user, widget_tagged_field, widget_user_tag):
        w = _make_db_widget(test_user, widget_tagged_field)
        result = w.render("field", None)

        assert "field" in result
