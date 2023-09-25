"""Test tags collections."""

import pytest
from django.core.exceptions import ValidationError
from hypothesis import given
from hypothesis import strategies as st

from tag_me.utils.collections import FieldTagListFormatter


class TestFieldTagListFormatter:
    """Test the tags FieldTagListFormatter."""

    # *************************    Add Tags    *******************************

    class TestAddTags:
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
            obj = FieldTagListFormatter("a,b,c")
            obj.add_tags(None)

            assert obj == ["a", "b", "c"]

    # *************************    Append Tags     ****************************

    class TestAppendTags:
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

    class TestDeleteTags:
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

    class TestErrors:
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
                "must be dict or list or set containing strings, or a string or None, type is"  # noqa: E501
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

            assert "must be type <class 'str'>, type is" in str(
                exc.value
            ).replace("\\", "")
            assert exc.type == ValidationError

        def test_unsupported_type_in_dict_raises_error(self):
            obj = FieldTagListFormatter("a,b,c")
            obj2 = {"tags": {"error": "here"}}
            with pytest.raises(ValidationError) as exc:
                obj.add_tags(obj2)
            assert (
                "{'tags': {'error': 'here'}} The field dict must contain a value type str or set[str] or list[str]. Keys supplied dict_keys(['tags']). Value type <class 'dict'>."  # noqa: E501
                in str(exc.value)
            )

            assert exc.type == ValidationError

        def test_missing_key_in_dict_raises_error(self):
            obj = FieldTagListFormatter("a,b,c")
            obj2 = {"error": "a,b,c"}
            with pytest.raises(ValidationError) as exc:
                obj.add_tags(obj2)
            assert (
                "{'error': 'a,b,c'} The field dict must contain the key 'tags' with a value type str or set[str] or list[str]. Keys supplied dict_keys(['error'])."  # noqa: E501
                in str(exc.value)
            )

            assert exc.type == ValidationError

    # *************************    Extend Tags     ****************************

    class TestExtendTags:
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

    class TestFormattedReturns:
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

    class TestInit:
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

    class TestInsertTags:
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

    class TestTagAnd__Methods:
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
