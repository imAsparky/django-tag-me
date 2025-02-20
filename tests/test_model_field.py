"""tag-me model field tests"""

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase
from hypothesis.extra.django import TestCase

from tag_me.db.models.fields import TagMeCharField
from tag_me.models import UserTag
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

    # Removed issue-108. tag-me bypasses Django choices validation. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_assignment_from_choice_enum(self):
    #     """Equivalent to Django test."""
    #
    #     class Event(models.TextChoices):
    #         C = "Carnival!"
    #         F = "Festival!"
    #
    #     tag_1 = TaggedFieldTestModel.objects.create(
    #         tagged_field_1=Event.C,
    #         tagged_field_2=Event.F,
    #     )
    #     tag_1.refresh_from_db()
    #     assert "Carnival!" == tag_1.tagged_field_1
    #     assert "Festival!" == tag_1.tagged_field_2
    #     assert Event.C == tag_1.tagged_field_1
    #     assert Event.F == tag_1.tagged_field_2
    #     tag_2 = TaggedFieldTestModel.objects.get(
    #         tagged_field_1="Carnival!",
    #     )
    #     assert tag_2 == tag_1
    #     assert Event.C == tag_2.tagged_field_1


class TestMethods(SimpleTestCase):
    """Equivalent to Django test."""

    def test_deconstruct(self):
        f = TagMeCharField()
        *_, kwargs = f.deconstruct()
        assert {"max_length": 255} == kwargs
        f = TagMeCharField(db_collation="utf8_esperanto_ci")
        *_, kwargs = f.deconstruct()
        assert {
            "db_collation": "utf8_esperanto_ci",
            "max_length": 255,
        } == kwargs


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

    # Removed issue-108. tag-me bypasses Django choices validation. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_charfield_with_choices_cleans_valid_choice(self):
    #     f = TagMeCharField(max_length=1, choices=[("a", "A"), ("b", "B")])
    #     assert f.clean("a", None) == "a"

    # Removed issue-108. tag-me does not use enum in choices. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_charfield_with_choices_raises_error_on_invalid_choice(self):
    #     f = TagMeCharField(choices=[("a", "A"), ("b", "B")])
    #     msg = "Value 'not a' is not a valid choice."
    #     with self.assertRaisesMessage(ValidationError, msg):
    #         f.clean("not a", None)

    # Removed issue-108. tag-me does not use enum in choices. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_enum_choices_cleans_valid_string(self):
    #     f = TagMeCharField(choices=self.Choices.choices, max_length=1)
    #     assert f.clean("c", None) == "c"

    # Removed issue-108. tag-me does not use enum in choices. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_enum_choices_invalid_input(self):
    #     f = TagMeCharField(choices=self.Choices.choices, max_length=1)
    #     msg = "Value 'd' is not a valid choice."
    #     with self.assertRaisesMessage(ValidationError, msg):
    #         f.clean("d", None)
    #

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

    # Removed issue-108. tag-me bypasses Django choices validation. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_charfield_choice_not_valid_and_not_in_empty(self):
    #     f = TagMeCharField(choices=self.Choices.choices)
    #     value = "invalid"
    #
    #     with pytest.raises(ValidationError) as exc:
    #         f.clean(value, None)
    #     assert "Value 'invalid' is not a valid choice." in str(exc.value)
    #     assert exc.type == ValidationError

    # Removed issue-108. tag-me bypasses Django choices validation. The choices
    # are added to a FieldTagListFormatter instance.
    # def test_charfield_choice_in_empty_values(self):
    #     f = TagMeCharField(choices=self.Choices.choices)
    #
    #     with pytest.raises(ValidationError) as exc:
    #         f.clean(None, None)
    #     assert "This field cannot be null." in str(exc.value)
    #     assert exc.type == ValidationError
    #
    #     with pytest.raises(ValidationError) as exc:
    #         f.clean("", None)
    #     assert "This field cannot be blank." in str(exc.value)
    #     assert exc.type == ValidationError
    #     with pytest.raises(ValidationError) as exc:
    #         f.clean([], None)
    #     assert "This field cannot be blank." in str(exc.value)
    #     assert exc.type == ValidationError
    #     with pytest.raises(ValidationError) as exc:
    #         f.clean((), None)
    #     assert "This field cannot be blank." in str(exc.value)
    #     assert exc.type == ValidationError
    #     with pytest.raises(ValidationError) as exc:
    #         f.clean({}, None)
    #     assert "This field cannot be blank." in str(exc.value)
    #     assert exc.type == ValidationError


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

    # ..todo:: probably a duplicate of test in test_collections. Review in refactor
    # def test_tags_as_unsupported_input(self):
    #     test_uns1 = 5
    #     test_uns2 = 1.2
    #     test_uns3 = True
    #     f = TagMeCharField()
    #
    #     with pytest.raises(ValidationError) as exc:
    #         f.to_python(test_uns1)
    #
    #         assert "['5 is not type str, set, list or dict']" in str(
    #             exc.value
    #         ).replace("\\", "")
    #         assert exc.type == ValidationError
    #
    #     with pytest.raises(ValidationError) as exc:
    #         f.to_python(test_uns2)
    #
    #         assert "['1.2 is not type str, set, list or dict']" in str(
    #             exc.value
    #         ).replace("\\", "")
    #         assert exc.type == ValidationError
    #
    #     with pytest.raises(ValidationError) as exc:
    #         f.to_python(test_uns3)
    #
    #         assert "['True is not type str, set, list or dict']" in str(
    #             exc.value
    #         ).replace("\\", "")
    #         assert exc.type == ValidationError

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
        class Event(models.TextChoices):
            C = "Carnival!"
            F = "Festival!"

        f = TagMeCharField(choices=Event.choices)

        # Check internal representation of choices
        assert f._tag_choices == "Carnival!, Festival!,"

        # Check the choices are formatted and saved to the db correctly
        assert f.to_python(f._tag_choices) == "Carnival!, Festival!,"

        # Check Django choices machinery is disabled.
        assert f.choices is None

    def test_tags_input_is_choices_LIST(self):
        list_choices: list = [
            "Carnival!",
            "Festival!",
        ]
        f = TagMeCharField(choices=list_choices)

        # Check internal representation of choices
        assert f._tag_choices == "Carnival!, Festival!,"

        # Check the choices are formatted and saved to the db correctly
        assert f.to_python(f._tag_choices) == "Carnival!, Festival!,"

        # Check Django choices machinery is disabled.
        assert f.choices is None

    def test_tags_input_is_null_only_tags(self):
        null_tags = [
            "null",
            "Null",
            "NULL",
        ]

        f = TagMeCharField()

        assert f.to_python(null_tags) == ""

    # ..todo:: probably a duplicate of test in test_collections. Review in refactor
    # def test_tags_input_includes_null_tags(self):
    #     null_tags = [
    #         "null",
    #         "Null",
    #         "NULL",
    #         "Not Null",
    #         "Still Not Null",
    #     ]
    #
    #     f = TagMeCharField()
    #
    #     assert f.to_python(null_tags) == "Not Null, Still Not Null"


class TestTagMeCharFieldOtherMethods(TestCase):
    """Test other overridden Charfield Methods"""

    def test_default_form_field_form_class_widget(self):
        f = TagMeCharField()
        f.model = UserTag()
        assert (
            str(type(f.formfield()))
            == "<class 'tag_me.db.forms.fields.TagMeCharField'>"
        )

    def test_admin_form_field_form_class_widget(self):
        kwargs: dict[str, str] = {"widget": "django.contrib.admin.widgets"}

        f = TagMeCharField()
        f.model = UserTag()

        assert (
            str(type(f.formfield(**kwargs)))
            == "<class 'django.forms.fields.CharField'>"
        )
