"""
Tests for tag_me.forms.fields.TagMeCharField (the form field).

Note: This tests the Django *form* field, not the model field.
The model field tests are in test_model_field.py.

Covers:
    - to_python: empty, string, None, list input
    - Validators: max_length, min_length, null chars
    - State isolation: sequential calls don't leak tags
"""

from django.core import validators

from tag_me.forms.fields import TagMeCharField
from tag_me.utils.collections import FieldTagListFormatter


class TestFormFieldToPython:
    """Test form field to_python conversion."""

    def test_empty_string_returns_empty(self):
        f = TagMeCharField()
        assert f.to_python("") == ""

    def test_csv_string_input(self):
        f = TagMeCharField()
        expected = FieldTagListFormatter("a,b,c").toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python("a,b,c") == expected

    def test_none_input_returns_empty(self):
        f = TagMeCharField()
        assert f.to_python(None) == ""

    def test_list_input(self):
        f = TagMeCharField()
        expected = FieldTagListFormatter(["x", "y"]).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(["x", "y"]) == expected

    def test_sequential_calls_do_not_leak_state(self):
        """Calling to_python twice should not carry tags from the first call."""
        f = TagMeCharField()

        result1 = f.to_python("alpha,beta")
        result2 = f.to_python("gamma")

        assert "alpha" not in result2
        assert "beta" not in result2
        assert "gamma" in result2


class TestFormFieldValidators:
    """Test that standard Django validators are present."""

    def test_max_and_min_length_validators(self):
        f = TagMeCharField(min_length=1234, max_length=5678)

        assert any(isinstance(v, validators.MaxLengthValidator) for v in f.validators)
        assert any(isinstance(v, validators.MinLengthValidator) for v in f.validators)

    def test_null_character_validator(self):
        f = TagMeCharField(min_length=1, max_length=100)

        assert any(
            isinstance(v, validators.ProhibitNullCharactersValidator)
            for v in f.validators
        )
