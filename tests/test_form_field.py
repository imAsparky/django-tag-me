"""tag-me model field tests"""

from django.test import SimpleTestCase

from tag_me.db.forms.fields import TagMeCharFieldForm
from tag_me.utils.collections import FieldTagListFormatter


class TestTagMeCharFieldFormToPython(SimpleTestCase):
    def test_empty_value(self):
        f = TagMeCharFieldForm()

        assert f.to_python("") == ""

    def test_with_value(self):
        f = TagMeCharFieldForm()

        assert f.to_python("a,b,c") == FieldTagListFormatter("a,b,c").toCSV()


# After refactor these tests are redundant, here for reference. Can be deleted
# class TestTagMeCharFieldFormValidators(SimpleTestCase):
#     def test_no_min_max_but_default_validators(self):
#         cf = TagMeCharFieldForm()

#         assert not any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.MaxLengthValidator)
#         )
#         assert not any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.MinLengthValidator)
#         )
#         assert any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.ProhibitNullCharactersValidator)
#         )

#     def test_max_length_and_default_validator(self):
#         cf = TagMeCharFieldForm(max_length=1234)

#         assert any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.MaxLengthValidator)
#         )

#         assert any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.ProhibitNullCharactersValidator)
#         )

#     def test_min_length_and_default_validator(self):
#         cf = TagMeCharFieldForm(min_length=5)

#         assert any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.MinLengthValidator)
#         )
#         assert any(
#             x
#             for x in cf.validators
#             if isinstance(x, validators.ProhibitNullCharactersValidator)
#         )
