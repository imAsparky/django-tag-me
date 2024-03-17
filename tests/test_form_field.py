"""tag-me model field tests"""

from django.core import validators
from django.test import SimpleTestCase

from tag_me.db.forms.fields import TagMeCharField
from tag_me.utils.collections import FieldTagListFormatter


class TestTagMeCharFieldForm(SimpleTestCase):
    def test_empty_value(self):
        f = TagMeCharField()

        assert f.to_python("") == ""

    def test_with_value(self):
        f = TagMeCharField()

        assert f.to_python("a,b,c") == FieldTagListFormatter("a,b,c").toCSV(
            include_trailing_comma=True,
        )

    def test_validators(self):
        f = TagMeCharField(
            min_length=1234,
            max_length=5678,
        )

        assert any(
            x
            for x in f.validators
            if isinstance(x, validators.MaxLengthValidator)
        )

        assert any(
            x
            for x in f.validators
            if isinstance(x, validators.MinLengthValidator)
        )

        assert any(
            x
            for x in f.validators
            if isinstance(x, validators.ProhibitNullCharactersValidator)
        )
