"""Test tags collections."""

import pytest
from django.core.exceptions import ValidationError
from hypothesis import given
from hypothesis import strategies as st

from tag_me.utils.collections import FieldTagListFormatter


class TestTagCollectionsFieldTagListFormatter:
    """Test the tags FieldTagListFormatter."""

    # *************************    Add Tags    *******************************

    def test_add_tags_dict_of_list_no_dups(self):
        obj = FieldTagListFormatter()
        obj.add_tags({"tags": ["one", "one", "two", "two"]})

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_add_tags_dict_of_str_no_dups(self):
        obj = FieldTagListFormatter()
        obj.add_tags({"tags": "one, one, two, two"})

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_add_tags_list_no_dups(self):
        obj = FieldTagListFormatter()
        obj.add_tags(["one", "one", "two", "two"])

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    def test_add_tags_str_no_dups(self):
        obj = FieldTagListFormatter()
        obj.add_tags("one, one, two, two")

        assert obj.__len__() == 2
        assert obj.count("one") == 1
        assert obj.count("two") == 1

    # *************************    Append Tags     ****************************

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

    @given(
        objs=st.one_of(
            st.integers(),
            st.fractions(
                min_value=0,
                max_value=10,
                max_denominator=9,
            ),
        )
    )
    def test_unsupported_type_raises_error(self, objs):
        with pytest.raises(ValidationError) as exc:
            FieldTagListFormatter(objs)

        assert (
            "must be dict or list or set containing strings, or a string or None, type is"
            in str(exc.value)
        )
        assert exc.type == ValidationError

    @given(
        objs=st.lists(
            st.one_of(
                st.integers(),
                st.dictionaries(
                    keys=st.text().filter(lambda x: x not in ("tags")),
                    values=st.lists(st.text()),
                    dict_class=dict,
                    min_size=1,
                ),
            ),
            min_size=1,
        ),
    )
    def test_unsupported_type_in_list_raises_error(self, objs):
        with pytest.raises(ValidationError) as exc:
            FieldTagListFormatter(objs)

        assert "must be type <class 'str'>, type is" in str(exc.value).replace(
            "\\", ""
        )
        assert exc.type == ValidationError
        # assert 1 == 1

    # *************************    Extend Tags     ****************************

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

    # ***********************    Formated Returns    **************************

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

    # ****************************    Init   *********************************

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

    # ************************    Remove Tag    *******************************

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

    # ********************s******    Set Tag    ***********s*********************

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
