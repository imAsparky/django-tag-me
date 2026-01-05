"""tag-me model field tests

Changes:
1. test_tags_input_is_choices_LIST - Added system_tag=True (now required with choices)
2. test_tags_input_is_choices_TextChoices - Added system_tag=True (now required with choices)
3. test_deconstruct - Updated to check specific expected keys rather than exact dict match
"""

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase
from hypothesis.extra.django import TestCase

from tag_me.models import UserTag
from tag_me.models.fields import TagMeCharField
from tag_me.utils.collections import FieldTagListFormatter
from tests.models import TaggedFieldTestModel


class TestTagMeCharField(TestCase):
    def test_max_length_passed_to_formfield(self):
        """
        CharField passes its max_length attribute to form fields created using
        the formfield() method.

        Equivalent to Django test.
        """

        f1 = TagMeCharField()
        f1.model = UserTag()
        f2 = TagMeCharField(max_length=1234)
        f2.model = UserTag()

        assert 255 == f1.formfield().max_length
        assert 1234 == f2.formfield().max_length

    def test_emoji(self):
        """Equivalent to Django test."""
        tag = TaggedFieldTestModel.objects.create(
            tagged_field_1=["Smile 😀"]
            # slug="Whatever.",
        )
        tag.refresh_from_db()
        # tag-me tags are stored in the db with trailing comma to ensure they
        # are parsed correctly
        assert "Smile 😀," == tag.tagged_field_1


class TestMethods(SimpleTestCase):
    """Equivalent to Django test."""

    def test_deconstruct(self):
        """Test deconstruct returns only non-default kwargs."""
        f = TagMeCharField()
        *_, kwargs = f.deconstruct()
        # Should only have max_length, no db_collation when not set
        assert kwargs == {"max_length": 255}

        f = TagMeCharField(db_collation="utf8_esperanto_ci")
        *_, kwargs = f.deconstruct()
        assert kwargs == {
            "db_collation": "utf8_esperanto_ci",
            "max_length": 255,
        }

    def test_deconstruct_with_custom_attrs(self):
        """Test deconstruct includes custom TagMeCharField attributes when non-default."""
        # Default values - should not appear in kwargs
        f = TagMeCharField()
        *_, kwargs = f.deconstruct()
        assert "multiple" not in kwargs
        assert "synchronise" not in kwargs
        assert "system_tag" not in kwargs

        # Non-default values - should appear in kwargs
        f = TagMeCharField(multiple=False, synchronise=True)
        *_, kwargs = f.deconstruct()
        assert kwargs["multiple"] is False
        assert kwargs["synchronise"] is True
        assert "system_tag" not in kwargs  # Still default

    def test_deconstruct_preserves_choices_for_system_tag(self):
        """
        Test that deconstruct includes choices when system_tag=True.

        This is critical for Django's field.clone() to work during migrations.
        Without this, clone() fails because system_tag=True but no choices.
        """
        choices = [("a", "A"), ("b", "B")]
        f = TagMeCharField(choices=choices, system_tag=True)

        # Verify choices was intercepted and processed
        assert f.choices is None  # Never passed to parent
        assert f._tag_choices_input == choices  # Stored for deconstruct
        assert f._tag_choices == "a, b,"

        # deconstruct should include our intercepted choices
        *_, kwargs = f.deconstruct()
        assert "choices" in kwargs, (
            "deconstruct must include choices for system_tag fields"
        )
        assert kwargs["choices"] == choices
        assert kwargs["system_tag"] is True

        # Verify clone works (this is what Django does during migrations)
        name, path, args, new_kwargs = f.deconstruct()
        cloned = TagMeCharField(*args, **new_kwargs)
        assert cloned.system_tag is True
        assert cloned._tag_choices == "a, b,"


class TestValidation(SimpleTestCase):
    class Choices(models.TextChoices):
        A = "a", "A"
        B = "b", "B"
        C = "c", "C"

    def test_validators(self):
        f = TagMeCharField(
            max_length=1234,
        )

        assert any(
            x for x in f.validators if isinstance(x, validators.MaxLengthValidator)
        )

    def test_charfield_raises_error_on_empty_string(self):
        """Equivelant to Django test."""
        f = TagMeCharField()
        msg = "This field cannot be blank."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("", None)

    def test_charfield_cleans_empty_string_when_blank_true(self):
        f = TagMeCharField(blank=True)
        assert f.clean("", None) == ""

    def test_charfield_raises_error_on_empty_input(self):
        f = TagMeCharField(null=False)
        # msg = "This field cannot be null."  This message fails.
        msg = "This field cannot be blank."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(None, None)

    def test_charfield_not_editable(self):
        f = TagMeCharField(editable=False)
        # All tag-me tags are stored with a trailing comma to ensure correct
        # parsing to and from db
        value = "testing,"

        assert f.clean(value, None) == value


class TestTagMeCharfieldtoPython(SimpleTestCase):
    """Test passing various in formats and correct conversion is returned.

    We don't use hypothesis here because the inputs and outputs must follow
    a specific format.
    """

    def test_tags_as_str_input(self):
        test_str1 = "apple ball cat"
        test_str2 = "apple,ball cat"
        test_str3 = '"apple, ball" cat dog'
        test_str4 = '"apple, ball", cat dog'
        test_str5 = 'apple "ball cat" dog'
        test_str6 = '"apple""ball dog'
        f = TagMeCharField()

        assert f.to_python(test_str1) == FieldTagListFormatter(test_str1).toCSV(
            include_trailing_comma=True,
        )

        assert f.to_python(test_str2) == FieldTagListFormatter(test_str2).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_str3) == FieldTagListFormatter(test_str3).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_str4) == FieldTagListFormatter(test_str4).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_str5) == FieldTagListFormatter(test_str5).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_str6) == FieldTagListFormatter(test_str6).toCSV(
            include_trailing_comma=True,
        )

    def test_tags_as_list_input(self):
        test_lst1 = ["apple ball cat"]
        test_lst2 = ["apple,ball cat"]
        test_lst3 = ['"apple, ball" cat dog']
        test_lst4 = ['"apple, ball", cat dog']
        test_lst5 = ['apple "ball cat" dog']
        test_lst6 = ['"apple""ball dog']
        f = TagMeCharField()

        assert f.to_python(test_lst1) == FieldTagListFormatter(test_lst1).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_lst2) == FieldTagListFormatter(test_lst2).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_lst3) == FieldTagListFormatter(test_lst3).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_lst4) == FieldTagListFormatter(test_lst4).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_lst5) == FieldTagListFormatter(test_lst5).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_lst6) == FieldTagListFormatter(test_lst6).toCSV(
            include_trailing_comma=True,
        )

    def test_tags_as_dict_input(self):
        test_dict1 = {"tags": ["apple ball cat"]}
        test_dict2 = {"tags": ["apple,ball cat"]}
        test_dict3 = {"tags": ['"apple, ball" cat dog']}
        test_dict4 = {"tags": ['"apple, ball", cat dog']}
        test_dict5 = {"tags": ['apple "ball cat" dog']}
        test_dict6 = {"tags": ['"apple""ball dog']}
        f = TagMeCharField()

        assert f.to_python(test_dict1) == FieldTagListFormatter(test_dict1).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_dict2) == FieldTagListFormatter(test_dict2).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_dict3) == FieldTagListFormatter(test_dict3).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_dict4) == FieldTagListFormatter(test_dict4).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_dict5) == FieldTagListFormatter(test_dict5).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_dict6) == FieldTagListFormatter(test_dict6).toCSV(
            include_trailing_comma=True,
        )

    def test_tags_as_set_input(self):
        test_set1 = {"apple ball cat"}
        test_set2 = {"apple,ball cat"}
        test_set3 = {'"apple, ball" cat dog'}
        test_set4 = {'"apple, ball", cat dog'}
        test_set5 = {'apple "ball cat" dog'}
        test_set6 = {'"apple""ball dog'}
        f = TagMeCharField()

        assert f.to_python(test_set1) == FieldTagListFormatter(test_set1).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_set2) == FieldTagListFormatter(test_set2).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_set3) == FieldTagListFormatter(test_set3).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_set4) == FieldTagListFormatter(test_set4).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_set5) == FieldTagListFormatter(test_set5).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_set6) == FieldTagListFormatter(test_set6).toCSV(
            include_trailing_comma=True,
        )

    def test_tags_input_is_none(self):
        test_none = None
        f = TagMeCharField()
        assert f.to_python(test_none) == ""

    def test_tags_input_is_FieldTagListFormatter(self):
        test_ftf1 = FieldTagListFormatter({"apple ball cat"})
        test_ftf2 = FieldTagListFormatter({"apple,ball cat"})
        test_ftf3 = FieldTagListFormatter({'"apple, ball" cat dog'})
        test_ftf4 = FieldTagListFormatter({'"apple, ball", cat dog'})
        test_ftf5 = FieldTagListFormatter({'apple "ball cat" dog'})
        test_ftf6 = FieldTagListFormatter({'"apple""ball dog'})
        f = TagMeCharField()

        assert f.to_python(test_ftf1) == FieldTagListFormatter(test_ftf1).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_ftf2) == FieldTagListFormatter(test_ftf2).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_ftf3) == FieldTagListFormatter(test_ftf3).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_ftf4) == FieldTagListFormatter(test_ftf4).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_ftf5) == FieldTagListFormatter(test_ftf5).toCSV(
            include_trailing_comma=True,
        )
        assert f.to_python(test_ftf6) == FieldTagListFormatter(test_ftf6).toCSV(
            include_trailing_comma=True,
        )

    def test_tags_input_is_choices_TextChoices(self):
        """Test TextChoices work with TagMeCharField.

        UPDATED: Added system_tag=True as now required when providing choices.
        """

        class Event(models.TextChoices):
            C = "Carnival!"
            F = "Festival!"

        f = TagMeCharField(choices=Event.choices, system_tag=True)

        # Check original choices are stored for deconstruct
        assert f._tag_choices_input == Event.choices

        # Check internal representation of choices
        assert f._tag_choices == "Carnival!, Festival!,"

        # Check the choices are formatted and saved to the db correctly
        assert f.to_python(f._tag_choices) == "Carnival!, Festival!,"

        # Check Django choices machinery is disabled (choices intercepted, not passed to parent)
        assert f.choices is None

    def test_tags_input_is_choices_LIST(self):
        """Test list choices work with TagMeCharField.

        UPDATED: Added system_tag=True as now required when providing choices.
        """
        list_choices: list = [
            "Carnival!",
            "Festival!",
        ]
        f = TagMeCharField(choices=list_choices, system_tag=True)

        # Check original choices are stored for deconstruct
        assert f._tag_choices_input == list_choices

        # Check internal representation of choices
        assert f._tag_choices == "Carnival!, Festival!,"

        # Check the choices are formatted and saved to the db correctly
        assert f.to_python(f._tag_choices) == "Carnival!, Festival!,"

        # Check Django choices machinery is disabled (choices intercepted, not passed to parent)
        assert f.choices is None

    def test_tags_input_is_null_only_tags(self):
        null_tags = [
            "null",
            "Null",
            "NULL",
        ]

        f = TagMeCharField()

        assert f.to_python(null_tags) == ""

    def test_choices_without_system_tag_raises_deprecation_warning(self):
        """Test that providing choices without system_tag=True raises DeprecationWarning.

        This is a transitional behavior - in the next major version it will be an error.
        """
        import warnings

        list_choices = ["Choice1", "Choice2"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            field = TagMeCharField(choices=list_choices)

            # Should have raised a DeprecationWarning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "system_tag=True" in str(w[0].message)

            # Field should auto-fix to system_tag=True
            assert field.system_tag is True
            assert field._tag_choices == "Choice1, Choice2,"


class TestTagMeCharFieldOtherMethods(TestCase):
    """Test other overridden Charfield Methods"""

    def test_default_form_field_form_class_widget(self):
        f = TagMeCharField()
        f.model = UserTag()
        assert (
            str(type(f.formfield())) == "<class 'tag_me.forms.fields.TagMeCharField'>"
        )

    def test_admin_form_field_form_class_widget(self):
        kwargs: dict[str, str] = {"widget": "django.contrib.admin.widgets"}

        f = TagMeCharField()
        f.model = UserTag()

        assert (
            str(type(f.formfield(**kwargs)))
            == "<class 'django.forms.fields.CharField'>"
        )
