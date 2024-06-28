"""Test tags collections."""

import re
import unittest.mock as mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from tag_me.utils.collections import FieldTagListFormatter

# Some tests are slow due to console logging of errors.
# Adjust this time if you get hypothesis flakey test failures
# 600 milliseconds is usually enough.
TEST_DEADLINE_TIME = 600

null_pattern = re.compile(
    r"\bnull\b[\.,]?", re.IGNORECASE
)  # Matches 'null' variants


# *******************    Generate hypothesis data    *************************
def valid_tag_dictionaries(min_size=1):
    """
    Generates non-empty dictionaries with a 'tags' key, ensuring a minimum
    number of key-value pairs.

    :param min_size: The minimum number of key-value pairs in the generated
                     dictionaries. (Defaults to 1).

    :returns: A Hypothesis strategy that generates valid tag dictionaries.
    """

    return st.dictionaries(
        keys=st.just("tags"),
        values=st.one_of(
            st.text(min_size=1),
            st.lists(st.text(min_size=1)),
        ),
        min_size=min_size,
    ).filter(lambda d: d)


def invalid_tags_dictionaries(min_size=1, max_size=2):
    """
    Generates dictionaries with a 'tags' key containing invalid value types
    (integers, floats, booleans, or lists of those types).  The size of any
    generated list will be controlled by the min_size and max_size parameters.

    :param min_size: The minimum size of generated lists (defaults to 1).
    :param max_size: The maximum size of generated lists (defaults to 2).

    :returns: A Hypothesis strategy that generates dictionaries with invalid tag values.
    """

    return st.dictionaries(
        keys=st.just("tags"),
        values=st.one_of(
            st.integers(),
            st.floats(),
            st.booleans(),
            st.lists(
                st.integers(),
                min_size=min_size,
                max_size=max_size,
            ),
            st.lists(
                st.floats(),
                min_size=min_size,
                max_size=max_size,
            ),
            st.lists(
                st.booleans(),
                min_size=min_size,
                max_size=max_size,
            ),
        ),
    ).filter(lambda tags: tags != {})


class BaseFormatterTest(SimpleTestCase):
    def setUp(self):
        self.formatter = FieldTagListFormatter()


# *************************    Add Tags    *******************************


class TestAddTags(BaseFormatterTest):
    def test_add_tags_dict_of_list_no_dups(self):
        # obj = self.formatter
        obj = self.formatter.add_tags({"tags": ["one", "one", "two", "two"]})

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_add_tags_dict_of_str_no_dups(self):
        # obj = self.formatter
        obj = self.formatter.add_tags({"tags": "one, one, two, two"})

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_add_tags_list_no_dups(self):
        # obj = self.formatter
        obj = self.formatter.add_tags(["one", "one", "two", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_add_tags_str_no_dups(self):
        # obj = self.formatter
        obj = self.formatter.add_tags("one, one, two, two")

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test__add__FieldTagListFormatter(self):
        a = FieldTagListFormatter("a,b,c")
        b = FieldTagListFormatter("d,e,f")
        c = a + b

        d = FieldTagListFormatter("a,b,c,d,e,f,x,y,z")
        e = c + d

        assert c == ["a", "b", "c", "d", "e", "f"]
        assert e == ["a", "b", "c", "d", "e", "f", "x", "y", "z"]

    def test__add__list(self):
        a = FieldTagListFormatter("a,b,c")
        b = ["d", "e", "f"]
        c = a + b

        d = ["a", "b", "c", "d", "e", "f", "x", "y", "z"]
        e = c + d
        assert c == ["a", "b", "c", "d", "e", "f"]
        assert e == ["a", "b", "c", "d", "e", "f", "x", "y", "z"]

    def test__add__str(self):
        a = FieldTagListFormatter("a,b,c")
        b = "d"
        c = "a"
        d = a + b + c

        assert d == ["a", "b", "c", "d"]

    def test__radd__str(self):
        a = FieldTagListFormatter("a,b,c")
        b = FieldTagListFormatter("d,e,f")
        c = ["d", "e", "f"]
        d = "d"

        assert a.__radd__(b) == ["a", "b", "c", "d", "e", "f"]
        assert a.__radd__(c) == ["a", "b", "c", "d", "e", "f"]
        assert a.__radd__(d) == ["a", "b", "c", "d"]

    def test_add_None_returns_unchanged(self):
        obj = self.formatter
        obj.add_tags("a,b,c")
        obj.add_tags(None)

        assert obj == ["a", "b", "c"]

    # *************************    Append Tags     ****************************


class TestAppendTags(BaseFormatterTest):
    def test_append_tags_dict_of_list_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        obj.append({"tags": ["two", "three"]})
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_append_tags_dict_of_str_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        obj.append({"tags": "two, three"})
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_append_tags_list_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        obj.append(["two", "three"])
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_append_tags_set_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        obj.append({"two", "three"})
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_append_tags_str_no_dups(self):
        obj = FieldTagListFormatter("one, two")

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        obj.append("two, three")
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1


# **************************    Del Tags   ********************************


class TestDeleteTags(BaseFormatterTest):
    def test__delitem__(self):
        obj = FieldTagListFormatter("a,b,c")
        obj.__delitem__(2)

        assert obj == ["a", "b"]

    def test_del_tags_dict_of_list(self):
        obj = FieldTagListFormatter(["one", "two", "three"])

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.del_tags({"tags": ["two", "three"]})
        assert obj.__len__() == 1
        assert obj.count("one") == 1
        assert obj.count("two") == 0
        assert obj.count("three") == 0

    def test_del_tags_dict_of_str(self):
        obj = FieldTagListFormatter(["one", "two", "three"])

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.del_tags({"tags": "two, three"})
        assert obj.__len__() == 1
        assert obj.count("one") == 1
        assert obj.count("two") == 0
        assert obj.count("three") == 0

    def test_del_tags_list(self):
        obj = FieldTagListFormatter(["one", "two", "three"])

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.del_tags(["two", "three"])

        assert obj.__len__() == 1
        assert obj.count("one") == 1
        assert obj.count("two") == 0
        assert obj.count("three") == 0

    def test_del_tags_set(self):
        obj = FieldTagListFormatter(["one", "two", "three"])

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.del_tags({"two", "three"})

        assert obj.__len__() == 1
        assert obj.count("one") == 1
        assert obj.count("two") == 0
        assert obj.count("three") == 0

    def test_del_tags_str(self):
        obj = FieldTagListFormatter("one, two, three")

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.del_tags("two, three")

        assert obj.__len__() == 1
        assert obj.count("one") == 1
        assert obj.count("two") == 0
        assert obj.count("three") == 0


# ************************    Errors    ***********************************


class TestErrors(BaseFormatterTest):
    @mock.patch("tag_me.utils.collections.FieldTagListFormatter.logger")
    @h_settings(deadline=TEST_DEADLINE_TIME)
    @given(
        st.one_of(
            st.integers(),
            st.fractions(
                min_value=0,
                max_value=10,
                max_denominator=9,
            ),
        )
    )
    def test_unsupported_type_logs_error(self, mock_logger, tags):

        response = FieldTagListFormatter(tags)
        error_message = f"""
                        {mock_logger.error.call_args.args[0]}
                        {mock_logger.error.call_args.args[1]}
                        """
        error_pattern = re.compile(
            r"An invalid tag or container was passed (.*)"
        )
        assert error_pattern.search(error_message)
        assert response == []

    @mock.patch("tag_me.utils.collections.FieldTagListFormatter.logger")
    @h_settings(deadline=TEST_DEADLINE_TIME)
    @given(
        st.lists(
            st.one_of(
                st.integers(),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=2),
                    values=st.text(min_size=1, max_size=2),
                ),
                st.booleans(),
            ),
            min_size=1,
        ),
    )
    def test_unsupported_type_in_list_logs_error(self, mock_logger, list):

        response = FieldTagListFormatter(list)
        error_message = f"""
                        {mock_logger.error.call_args.args[0]}
                        {mock_logger.error.call_args.args[1]}
                        """
        error_pattern = re.compile(
            r"An invalid tag or container was passed (.*)"
        )
        assert error_pattern.search(error_message)
        assert response == []


# *************************    Extend Tags     ****************************


class TestExtendTags(BaseFormatterTest):
    def test_extend_tags_dict_of_list_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        extend = {"tags": ["two", "three"]}
        obj.extend(extend)
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_extend_tags_dict_of_str_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        extend = {"tags": "two, three"}
        obj.extend(extend)
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_extend_tags_list_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        extend = ["two", "three"]
        obj.extend(extend)
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_extend_tags_set_no_dups(self):
        obj = FieldTagListFormatter(["one", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        extend = {"two", "three"}
        obj.extend(extend)
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_extend_tags_str_no_dups(self):
        obj = FieldTagListFormatter("one, two")

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

        extend = "two, three"
        obj.extend(extend)
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1


# ***********************    Formatted Returns    *************************


class TestFormattedReturns(BaseFormatterTest):
    def test_returned_tags_are_sorted(self):
        tags = FieldTagListFormatter("zero, one, nine, ")

        assert tags == ["nine", "one", "zero"]

    def test_toCSV_no_trailing_comma(self):
        tags = FieldTagListFormatter("one, two")

        assert tags.toCSV(include_trailing_comma=False) == "one, two"

    def test_toCSV_with_trailing_comma(self):
        tags = FieldTagListFormatter("one, two")

        assert tags.toCSV(include_trailing_comma=True) == "one, two,"

    def test_toDict(self):
        tags = FieldTagListFormatter("one, two")

        assert tags.toDict() == {"tags": ["one", "two"]}

    def test_toJson(self):
        tags = FieldTagListFormatter("one, two")

        assert tags.toJson() == '{"tags": ["one", "two"]}'

    def test_toList(self):
        tags = FieldTagListFormatter("one, two")

        assert tags.toList() == ["one", "two"]

    def test_loose_comma(self):
        tags = FieldTagListFormatter("a,b,c,,")

        assert tags == ["a", "b", "c"]

    def test_open_quote_and_loose_comma(self):
        tags = FieldTagListFormatter(',"a,b,c,')

        assert tags == ["a", "b", "c"]

    def test_space_delimited(self):
        tags = FieldTagListFormatter("a c b")

        assert tags == ["a", "b", "c"]

    def test_space_delimited_tags(self):
        tags = FieldTagListFormatter('"tag1 double" tag2')

        assert tags == ["tag1 double", "tag2"]
        # assert 1 == 1

    def test_word_creation(self):
        tags = FieldTagListFormatter('"tag"')

        assert tags == ["tag"]


# ****************************    Init   *********************************


class TestInit(BaseFormatterTest):
    def test_init_dict_no_dups(self):
        obj = FieldTagListFormatter({"tags": ["one", "one", "two", "two"]})

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_init_list_no_dups(self):
        obj = FieldTagListFormatter(["one", "one", "two", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_init_none(self):
        obj = FieldTagListFormatter()

        assert obj.__len__() == 0

    def test_init_str_no_dups(self):
        obj = FieldTagListFormatter("one, one, two, two")

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1


# **************************    Insert Tag    *****************************


class TestInsertTags(BaseFormatterTest):
    def test_insert_tag_to_list_no_dups(self):
        obj = FieldTagListFormatter(["one", "two", "three"])

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.insert(0, "three")
        assert obj.__len__() == 3
        assert obj[0] == "one"
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_insert_tag_to_list(self):
        obj = FieldTagListFormatter(["one", "two", "three"])

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.insert(0, "zero")
        assert obj.__len__() == 4
        assert obj[0] == "zero"
        assert obj.count("zero") == 1
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1


# ****************     Other Tag  and __ Methods    ***********************


class TestTagAnd__Methods(BaseFormatterTest):
    def test__contains__(self):
        obj = FieldTagListFormatter("a,b,c")

        assert "a" in obj

    def test_copy(self):
        obj = FieldTagListFormatter("a,b,c")
        obj2 = obj.copy()

        assert obj == obj2

    def test_clear(self):
        obj = FieldTagListFormatter("a,b,c")
        obj.clear()

        assert obj.tags == []

    def test__ge__(self):
        obj = FieldTagListFormatter("a,b,c")
        obj2 = obj.copy()
        obj3 = FieldTagListFormatter("a,b")

        assert obj.__ge__(obj2)
        assert obj.__ge__(obj3)

    def test__getitem__(self):
        obj = FieldTagListFormatter("a,b,c,d,e,f,g,h")

        assert obj[3:5] == ["d", "e"]
        assert obj[6] == "g"

    def test__gt__(self):
        obj = FieldTagListFormatter("a,b,c")
        obj2 = FieldTagListFormatter("a,b")

        assert obj.__gt__(obj2)

    def test__iad__(self):
        obj = FieldTagListFormatter("a,b,c")
        obj2 = FieldTagListFormatter("d,e,f")
        obj3 = ["d", "e", "f"]

        assert obj.__iadd__(obj2) == ["a", "b", "c", "d", "e", "f"]

        obj = FieldTagListFormatter("a,b,c")
        obj3 = ["d", "e", "f"]
        assert obj.__iadd__(obj3) == ["a", "b", "c", "d", "e", "f"]

        obj = FieldTagListFormatter("a,b,c")
        obj4 = "z"
        assert obj.__iadd__(obj4) == ["a", "b", "c", "z"]

    def test__imul__(self):
        obj = FieldTagListFormatter("a,b,c")

        assert obj.__imul__(2) == ["a", "b", "c", "a", "b", "c"]

    def test_index(self):
        obj = FieldTagListFormatter("a,b,c")

        assert obj.index("b") == 1

    def test__le__(self):
        obj = FieldTagListFormatter("a,b,c")
        obj2 = obj.copy()
        obj3 = FieldTagListFormatter("a,b,c,d")

        assert obj.__le__(obj2)
        assert obj.__le__(obj3)

    def test__len__(self):
        obj = FieldTagListFormatter("a,b,c")

        assert obj.__len__() == 3

    def test__lt__(self):
        obj = FieldTagListFormatter("a,b,c")
        obj2 = FieldTagListFormatter("a,b,c,d")

        assert obj.__lt__(obj2)

    def test__mul__(self):
        obj = FieldTagListFormatter("a,b,c")

        assert obj.__mul__(2) == ["a", "b", "c", "a", "b", "c"]

    def test_pop(self):
        obj = FieldTagListFormatter("a,b,c,d,e,f")

        # Test default removes the last item
        obj.pop()
        assert obj == ["a", "b", "c", "d", "e"]

        obj.pop(0)
        assert obj == ["b", "c", "d", "e"]

    def test__repr__(self):
        a = FieldTagListFormatter("a,b,c")

        assert a.__repr__() == "['a', 'b', 'c']"

    def test_reverse(self):
        obj = FieldTagListFormatter("a,b,c,d,e,f")
        obj.reverse()

        assert obj == ["f", "e", "d", "c", "b", "a"]

    def test_sort(self):
        obj = FieldTagListFormatter("f,d,e,a,c,b")
        obj.sort()

        assert obj == ["a", "b", "c", "d", "e", "f"]

    # ************************    Remove Tag    ***************************

    def test_remove_item(self):
        obj = FieldTagListFormatter("one, two, three")

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj.remove("one")

        assert obj.__len__() == 2
        assert obj.count("one") == 0
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    #
    # ********************s******    Set Tag    ***************************

    def test_setitem_no_dups(self):
        obj = FieldTagListFormatter("one, two, three")

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj[0] = "two"
        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

    def test_setitem(self):
        obj = FieldTagListFormatter("one, two, three")

        assert obj.__len__() == 3
        assert obj.count("one") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1

        obj[0] = "New Tag"

        assert obj.__len__() == 3
        assert obj.count("New Tag") == 1
        assert obj.count("two") == 1
        assert obj.count("three") == 1


# ------ Specialized Test Classes ------
class TestIsValidTagContainer(BaseFormatterTest):

    @given(
        st.one_of(
            st.dictionaries(
                keys=st.just("tags"),
                # values=st.text(min_size=1),
                values=st.just(["v1", "v2"]),
            ).filter(lambda tags: tags != {}),
            st.lists(st.text()),
            st.sets(st.text()),
            st.text(),
            st.none(),
        )
    )
    def test_valid_tag_container(self, tags):
        assert self.formatter._is_valid_tag_container(tags)

    def test_invalid_dict_tag_container(self):
        invalid_dict = {"key": "value"}  # Example without 'tags'
        with self.assertRaises(ValidationError):
            self.formatter._is_valid_tag_container(invalid_dict)


class TestIsValidTag(BaseFormatterTest):

    @given(st.text())
    def test_valid_strings(self, tag):
        assert self.formatter._is_valid_tag(tag)

    def test_invalid_null_variants(self):
        invalid_tags = ["null", "NULL", "Null", "null.", "null,"]
        for tag in invalid_tags:
            assert not self.formatter._is_valid_tag(tag)

    @given(st.one_of(st.integers(), st.floats(), st.booleans(), st.none()))
    def test_invalid_non_strings(self, value):
        assert not self.formatter._is_valid_tag(value)


class TestIsValidTagList(BaseFormatterTest):

    @given(
        st.lists(
            st.text().filter(
                lambda x: not null_pattern.match(x)
            ),  # Regex filter
            min_size=1,
        )
    )
    def test_valid_tag_list(self, tag_list):
        assert self.formatter._is_valid_tag_list(tag_list)

    @given(
        st.lists(
            st.one_of(st.text(), st.from_regex(null_pattern)),
            min_size=1,
        ).filter(lambda x: any(null_pattern.match(tag) for tag in x))
    )
    def test_invalid_tag_list(self, tag_list):
        assert not self.formatter._is_valid_tag_list(tag_list)

    def test_empty_tag_list(self):  # Keep for the edge case
        assert self.formatter._is_valid_tag_list([])


class TestExtractTagsFromDict(BaseFormatterTest):

    @given(valid_tag_dictionaries())
    def test_valid_dicts(self, tags):
        result = self.formatter._extract_tags_from_dict(tags)
        assert isinstance(result, list)

    @h_settings(deadline=TEST_DEADLINE_TIME)
    @given(
        st.dictionaries(keys=st.text(), values=st.text()).filter(
            lambda d: "tags" not in d
        )
    )
    def test_dict_missing_tags_key(self, tags):
        result = self.formatter._extract_tags_from_dict(tags)
        assert isinstance(result, list)

    # .. todo:: h_settings: logging to cli takes time, follow up with logging/exceptions work package
    @h_settings(deadline=TEST_DEADLINE_TIME)
    @given(invalid_tags_dictionaries())
    def test_dict_with_invalid_values(self, tags):

        result = self.formatter._extract_tags_from_dict(tags)
        assert isinstance(result, list)

    # .. todo:: h_settings: logging to cli takes time, follow up with logging/exceptions work package
    @mock.patch("tag_me.utils.collections.FieldTagListFormatter.logger")
    @h_settings(deadline=TEST_DEADLINE_TIME)
    @given(invalid_tags_dictionaries())
    def test_logging_on_error(self, mock_logger, tags):

        self.formatter._extract_tags_from_dict(tags)

        error_message = f"""
                            {mock_logger.error.call_args.args[0]}
                            {mock_logger.error.call_args.args[1]}
                            """
        error_pattern = re.compile(r"An invalid dictionary was passed (.*)")
        assert error_pattern.search(error_message)
