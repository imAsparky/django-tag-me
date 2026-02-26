"""
Tests for TagMeCharField (tag_me.models.fields).

Covers:
    - Initialization: system_tag/choices validation, deprecation warning
    - Deconstruct: migration serialization round-trip
    - Validation: max_length, blank, null, editable
    - to_python: str, list, dict, set, None, FieldTagListFormatter, choices, null tags
    - get_prep_value: preparation for database storage
    - from_db_value: unit conversion + emoji/Unicode DB round-trip
    - formfield: widget type, kwargs merging, placeholder fallback
    - Thread safety: concurrent from_db_value, get_prep_value, to_python

Tests absorbed from test_deep_review_fixes.py:
    - TestTagMeCharFieldInit
    - TestDeconstruct
    - TestFormfieldKwargs
    - TestThreadSafety

Run with: pytest tests/test_model_field.py -v
"""

import concurrent.futures
import threading
import warnings

import pytest
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models

from tag_me.forms.fields import TagMeCharField as TagMeFormCharField
from tag_me.models.fields import TagMeCharField
from tag_me.utils.collections import FieldTagListFormatter
from tests.models import TaggedFieldTestModel


# =============================================================================
# Initialization
# =============================================================================


class TestTagMeCharFieldInit:
    """Test TagMeCharField __init__ argument handling."""

    def test_system_tag_requires_choices(self):
        with pytest.raises(ValueError, match="requires 'choices'"):
            TagMeCharField(system_tag=True)

    def test_empty_choices_with_system_tag_raises(self):
        with pytest.raises(ValueError, match="choices"):
            TagMeCharField(choices=[], system_tag=True)

    def test_empty_choices_without_system_tag_raises(self):
        with pytest.raises(ValueError, match="cannot be an empty list"):
            TagMeCharField(choices=[])

    def test_choices_without_system_tag_emits_deprecation_warning(self):
        """Providing choices without system_tag=True should warn and auto-fix."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            field = TagMeCharField(choices=["Choice1", "Choice2"])

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "system_tag=True" in str(w[0].message)
            assert field.system_tag is True
            assert field._tag_choices == "Choice1, Choice2,"

    def test_choices_as_django_tuples(self):
        field = TagMeCharField(
            choices=[("val1", "Label 1"), ("val2", "Label 2")],
            system_tag=True,
        )

        assert "val1" in field._tag_choices
        assert "val2" in field._tag_choices

    def test_choices_as_simple_list(self):
        field = TagMeCharField(
            choices=["simple1", "simple2"],
            system_tag=True,
        )

        assert "simple1" in field._tag_choices
        assert "simple2" in field._tag_choices

    def test_choices_as_text_choices(self):
        class Event(models.TextChoices):
            C = "Carnival!"
            F = "Festival!"

        field = TagMeCharField(choices=Event.choices, system_tag=True)

        assert field._tag_choices_input == Event.choices
        assert field._tag_choices == "Carnival!, Festival!,"
        # Django choices machinery is disabled — choices intercepted
        assert field.choices is None

    def test_choices_as_list_stores_input_for_deconstruct(self):
        list_choices = ["Carnival!", "Festival!"]
        field = TagMeCharField(choices=list_choices, system_tag=True)

        assert field._tag_choices_input == list_choices
        assert field._tag_choices == "Carnival!, Festival!,"
        assert field.choices is None

    def test_default_max_length_is_255(self):
        field = TagMeCharField()
        assert field.max_length == 255

    def test_explicit_max_length_honoured(self):
        field = TagMeCharField(max_length=500)
        assert field.max_length == 500

    def test_default_attribute_values(self):
        field = TagMeCharField()
        assert field.multiple is True
        assert field.synchronise is False
        assert field.system_tag is False
        assert field._tag_choices == ""
        assert field.tag_type == "user"

    def test_system_tag_sets_tag_type(self):
        field = TagMeCharField(choices=["a"], system_tag=True)
        assert field.tag_type == "system"


# =============================================================================
# Deconstruct (migration serialization)
# =============================================================================


class TestDeconstruct:
    """Test field.deconstruct() for migration round-trip fidelity."""

    def test_default_field_only_has_max_length(self):
        f = TagMeCharField()
        *_, kwargs = f.deconstruct()
        assert kwargs == {"max_length": 255}

    def test_includes_db_collation_when_set(self):
        f = TagMeCharField(db_collation="utf8_esperanto_ci")
        *_, kwargs = f.deconstruct()
        assert kwargs == {"db_collation": "utf8_esperanto_ci", "max_length": 255}

    def test_excludes_default_custom_attrs(self):
        """multiple=True, synchronise=False, system_tag=False are defaults."""
        f = TagMeCharField()
        *_, kwargs = f.deconstruct()
        assert "multiple" not in kwargs
        assert "synchronise" not in kwargs
        assert "system_tag" not in kwargs

    def test_includes_non_default_custom_attrs(self):
        f = TagMeCharField(multiple=False, synchronise=True)
        *_, kwargs = f.deconstruct()
        assert kwargs["multiple"] is False
        assert kwargs["synchronise"] is True
        assert "system_tag" not in kwargs  # Still default

    def test_includes_choices_for_system_tag(self):
        """Critical for Django's field.clone() during migrations."""
        choices = [("a", "A"), ("b", "B")]
        f = TagMeCharField(choices=choices, system_tag=True)

        assert f.choices is None  # Not passed to parent
        assert f._tag_choices_input == choices
        assert f._tag_choices == "a, b,"

        *_, kwargs = f.deconstruct()
        assert kwargs["choices"] == choices
        assert kwargs["system_tag"] is True

    def test_clone_round_trip_with_choices(self):
        """Deconstructed kwargs should produce an equivalent field."""
        choices = [("a", "A"), ("b", "B")]
        original = TagMeCharField(choices=choices, system_tag=True)

        name, path, args, kwargs = original.deconstruct()
        cloned = TagMeCharField(*args, **kwargs)

        assert cloned.system_tag is True
        assert cloned._tag_choices == "a, b,"

    def test_includes_system_tag_when_true(self):
        f = TagMeCharField(choices=["tag1"], system_tag=True)
        *_, kwargs = f.deconstruct()
        assert kwargs.get("system_tag") is True

    def test_path_is_correct_import(self):
        f = TagMeCharField()
        _, path, *_ = f.deconstruct()
        assert "TagMeCharField" in path


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    """Test field-level validation (no database required)."""

    def test_max_length_validator_present(self):
        f = TagMeCharField(max_length=1234)
        assert any(isinstance(v, validators.MaxLengthValidator) for v in f.validators)

    def test_empty_string_raises_when_blank_false(self):
        f = TagMeCharField()
        with pytest.raises(ValidationError, match="cannot be blank"):
            f.clean("", None)

    def test_empty_string_allowed_when_blank_true(self):
        f = TagMeCharField(blank=True)
        assert f.clean("", None) == ""

    def test_none_raises_when_null_false(self):
        f = TagMeCharField(null=False)
        with pytest.raises(ValidationError, match="cannot be blank"):
            f.clean(None, None)

    def test_non_editable_field_returns_value_as_is(self):
        f = TagMeCharField(editable=False)
        assert f.clean("testing,", None) == "testing,"


# =============================================================================
# to_python
# =============================================================================


class TestToPython:
    """Test to_python conversion for all supported input types.

    Each test verifies that to_python produces the same output as
    FieldTagListFormatter.toCSV(include_trailing_comma=True) for the
    same input, ensuring consistency between the field and the formatter.
    """

    _STR_CASES = [
        "apple ball cat",
        "apple,ball cat",
        '"apple, ball" cat dog',
        '"apple, ball", cat dog',
        'apple "ball cat" dog',
        '"apple""ball dog',
    ]

    @pytest.mark.parametrize("tag_string", _STR_CASES)
    def test_string_input(self, tag_string):
        f = TagMeCharField()
        expected = FieldTagListFormatter(tag_string).toCSV(include_trailing_comma=True)
        assert f.to_python(tag_string) == expected

    @pytest.mark.parametrize("tag_string", _STR_CASES)
    def test_list_input(self, tag_string):
        f = TagMeCharField()
        tag_list = [tag_string]
        expected = FieldTagListFormatter(tag_list).toCSV(include_trailing_comma=True)
        assert f.to_python(tag_list) == expected

    @pytest.mark.parametrize("tag_string", _STR_CASES)
    def test_dict_input(self, tag_string):
        f = TagMeCharField()
        tag_dict = {"tags": [tag_string]}
        expected = FieldTagListFormatter(tag_dict).toCSV(include_trailing_comma=True)
        assert f.to_python(tag_dict) == expected

    @pytest.mark.parametrize("tag_string", _STR_CASES)
    def test_set_input(self, tag_string):
        f = TagMeCharField()
        tag_set = {tag_string}
        expected = FieldTagListFormatter(tag_set).toCSV(include_trailing_comma=True)
        assert f.to_python(tag_set) == expected

    @pytest.mark.parametrize("tag_string", _STR_CASES)
    def test_field_tag_list_formatter_input(self, tag_string):
        f = TagMeCharField()
        ftf = FieldTagListFormatter({tag_string})
        expected = FieldTagListFormatter(ftf).toCSV(include_trailing_comma=True)
        assert f.to_python(ftf) == expected

    def test_none_input_returns_empty_string(self):
        f = TagMeCharField()
        assert f.to_python(None) == ""

    def test_null_only_tags_return_empty_string(self):
        f = TagMeCharField()
        assert f.to_python(["null", "Null", "NULL"]) == ""

    def test_text_choices_round_trip(self):
        class Event(models.TextChoices):
            C = "Carnival!"
            F = "Festival!"

        f = TagMeCharField(choices=Event.choices, system_tag=True)
        assert f.to_python(f._tag_choices) == "Carnival!, Festival!,"

    def test_list_choices_round_trip(self):
        f = TagMeCharField(choices=["Carnival!", "Festival!"], system_tag=True)
        assert f.to_python(f._tag_choices) == "Carnival!, Festival!,"


# =============================================================================
# get_prep_value (database write preparation)
# =============================================================================


class TestGetPrepValue:
    """Test get_prep_value produces correctly formatted CSV for DB storage."""

    def test_string_input(self):
        f = TagMeCharField()
        result = f.get_prep_value("beta, alpha")
        assert result == "alpha, beta,"

    def test_none_input(self):
        f = TagMeCharField()
        result = f.get_prep_value(None)
        assert result == ""

    def test_empty_string_input(self):
        f = TagMeCharField()
        result = f.get_prep_value("")
        assert result == ""

    def test_trailing_comma_included(self):
        f = TagMeCharField()
        result = f.get_prep_value("single_tag")
        assert result.endswith(",")

    def test_tags_sorted(self):
        f = TagMeCharField()
        result = f.get_prep_value("zebra, alpha, mango")
        tags = [t.strip() for t in result.rstrip(",").split(",")]
        assert tags == sorted(tags)

    def test_duplicates_removed(self):
        f = TagMeCharField()
        result = f.get_prep_value("dup, dup, dup")
        assert result == "dup,"

    def test_matches_formatter_output(self):
        """get_prep_value should produce identical output to FieldTagListFormatter."""
        f = TagMeCharField()
        value = "cherry, apple, banana, apple"
        expected = FieldTagListFormatter(value).toCSV(include_trailing_comma=True)
        assert f.get_prep_value(value) == expected


# =============================================================================
# from_db_value (database read conversion)
# =============================================================================


class TestFromDbValue:
    """Test from_db_value conversion (unit tests, no DB required)."""

    def test_string_input(self):
        f = TagMeCharField()
        result = f.from_db_value("beta, alpha,", None, None)
        assert result == "alpha, beta,"

    def test_none_input(self):
        f = TagMeCharField()
        result = f.from_db_value(None, None, None)
        assert result == ""

    def test_empty_string_input(self):
        f = TagMeCharField()
        result = f.from_db_value("", None, None)
        assert result == ""

    def test_trailing_comma_included(self):
        f = TagMeCharField()
        result = f.from_db_value("tag1,", None, None)
        assert result.endswith(",")

    def test_matches_formatter_output(self):
        f = TagMeCharField()
        value = "cherry, apple,"
        expected = FieldTagListFormatter(value).toCSV(include_trailing_comma=True)
        assert f.from_db_value(value, None, None) == expected


@pytest.mark.django_db
class TestFromDbValueRoundTrip:
    """Test from_db_value via actual database round-trip."""

    def test_emoji_preserved(self):
        tag = TaggedFieldTestModel.objects.create(tagged_field_1=["Smile \U0001f600"])
        tag.refresh_from_db()
        assert tag.tagged_field_1 == "Smile \U0001f600,"

    def test_unicode_preserved(self):
        tag = TaggedFieldTestModel.objects.create(
            tagged_field_1=["\u00fc\u00f1\u00ef\u00e7\u00f6\u00f0\u00e9"]
        )
        tag.refresh_from_db()
        assert "\u00fc\u00f1\u00ef\u00e7\u00f6\u00f0\u00e9" in tag.tagged_field_1

    def test_multiple_tags_round_trip(self):
        tag = TaggedFieldTestModel.objects.create(
            tagged_field_1="cherry, apple, banana"
        )
        tag.refresh_from_db()
        # Should be sorted with trailing comma
        assert tag.tagged_field_1 == "apple, banana, cherry,"


# =============================================================================
# formfield
# =============================================================================


@pytest.mark.django_db
class TestFormfield:
    """Test formfield() method, widget selection, and kwargs merging.

    All tests need DB access because formfield() queries TaggedFieldModel
    via ContentType.objects.get_for_model().
    """

    def _make_field(self, **kwargs):
        """Create a TagMeCharField with name set (simulating contribute_to_class)."""
        f = TagMeCharField(**kwargs)
        f.name = "test_field"
        return f

    def test_default_form_class_is_tag_me(self):
        f = self._make_field()
        form_field = f.formfield()
        assert isinstance(form_field, TagMeFormCharField)

    def test_max_length_default(self):
        f = self._make_field()
        assert f.formfield().max_length == 255

    def test_max_length_custom(self):
        f = self._make_field(max_length=1234)
        assert f.formfield().max_length == 1234

    def test_admin_widget_returns_django_charfield(self):
        from django.forms.fields import CharField as DjangoCharField

        f = self._make_field()
        form_field = f.formfield(widget="django.contrib.admin.widgets")
        assert isinstance(form_field, DjangoCharField)
        assert not isinstance(form_field, TagMeFormCharField)

    def test_preserves_help_text(self):
        f = self._make_field()
        form_field = f.formfield(help_text="Custom help text")
        assert form_field.help_text == "Custom help text"

    def test_preserves_label(self):
        f = self._make_field()
        form_field = f.formfield(label="Custom Label")
        assert form_field.label == "Custom Label"

    def test_preserves_initial(self):
        f = self._make_field()
        form_field = f.formfield(initial="initial_tag,")
        assert form_field.initial == "initial_tag,"

    def test_placeholder_when_no_tagged_field_model(self):
        """When TaggedFieldModel lookup returns None, formfield uses a placeholder."""
        f = self._make_field()
        # No TaggedFieldModel exists for this field — should still return a form field
        form_field = f.formfield()
        assert form_field is not None
        assert isinstance(form_field, TagMeFormCharField)

    def test_no_model_attr_uses_placeholder(self):
        """Field not yet attached to a model — hits AttributeError path."""
        f = TagMeCharField()
        f.name = "orphan_field"
        # Don't set f.model — triggers the AttributeError fallback
        form_field = f.formfield()
        assert form_field is not None
        assert isinstance(form_field, TagMeFormCharField)

    def test_widget_receives_field_metadata(self):
        """Non-admin widget should receive field_name in attrs."""
        f = self._make_field()
        form_field = f.formfield()
        widget_attrs = form_field.widget.attrs
        assert widget_attrs["field_name"] == "test_field"

    def test_required_is_false(self):
        f = self._make_field()
        form_field = f.formfield()
        assert form_field.required is False


# =============================================================================
# Thread Safety
# =============================================================================


class TestThreadSafety:
    """Test that field methods use isolated formatter instances.

    Each method should be safe to call concurrently from multiple threads
    without cross-contamination of tag data.
    """

    def _run_concurrent(self, func, inputs, workers=10):
        """Run func concurrently and return (input, output) pairs.

        Uses a lock to protect the shared results list.
        """
        results = []
        lock = threading.Lock()

        def _call(value):
            result = func(value)
            with lock:
                results.append((value, result))

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_call, v) for v in inputs]
            concurrent.futures.wait(futures)

        return results

    def test_from_db_value_isolation(self):
        field = TagMeCharField()
        inputs = [f"tag{i}," for i in range(100)]

        results = self._run_concurrent(
            lambda v: field.from_db_value(v, None, None),
            inputs,
        )

        assert len(results) == 100
        for original, result in results:
            assert original.strip(",") in result

    def test_get_prep_value_isolation(self):
        field = TagMeCharField()
        inputs = [f"prep_tag{i}" for i in range(100)]

        results = self._run_concurrent(field.get_prep_value, inputs)

        assert len(results) == 100
        for original, result in results:
            assert original in result

    def test_to_python_isolation(self):
        field = TagMeCharField()
        inputs = [f"python_tag{i}," for i in range(100)]

        results = self._run_concurrent(field.to_python, inputs)

        assert len(results) == 100
        for original, result in results:
            assert original.strip(",") in result

    def test_no_cross_contamination(self):
        """Each thread's tag should appear only in its own result."""
        field = TagMeCharField()
        inputs = [f"unique_{i}" for i in range(50)]

        results = self._run_concurrent(field.to_python, inputs)

        for original, result in results:
            # Result should contain exactly one tag (the input)
            tags = [t.strip() for t in result.rstrip(",").split(",") if t.strip()]
            assert tags == [original], f"Expected [{original}] but got {tags}"
