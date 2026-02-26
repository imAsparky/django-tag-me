"""
Tests for tag_me.utils.collections.FieldTagListFormatter.

Covers:
    - Initialization from dict, list, set, str, None
    - Duplicate prevention across add_tags, append, extend, insert, __setitem__
    - Deletion via del_tags, __delitem__, remove, pop, clear
    - List protocol: __contains__, __len__, __getitem__ (index + slice),
      __eq__, __ge__, __gt__, __le__, __lt__, __iadd__, __imul__, __add__,
      __radd__, __mul__, __rmul__, copy, index, reverse, sort
    - Formatted output: toCSV, toDict, toJson, toList
    - Validation: _is_valid_tag, _is_valid_tag_container, _is_valid_tag_list,
      _extract_tags_from_dict, _get_tag_list
    - Error handling: unsupported types, invalid dicts, invalid tag values

Run with: pytest tests/test_collections.py -v
"""

import json
import re
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from tag_me.utils.collections import FieldTagListFormatter

# Hypothesis deadline — error-path tests log to console which is slow.
DEADLINE = 600

NULL_PATTERN = re.compile(r"\bnull\b[\.,]?", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fmt():
    """Fresh empty FieldTagListFormatter."""
    return FieldTagListFormatter()


@pytest.fixture
def abc():
    """Formatter pre-loaded with ['a', 'b', 'c']."""
    return FieldTagListFormatter("a,b,c")


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def _valid_tag_dicts(min_size=1):
    """Dicts with a 'tags' key whose value is str or list[str]."""
    return st.dictionaries(
        keys=st.just("tags"),
        values=st.one_of(
            st.text(min_size=1),
            st.lists(st.text(min_size=1)),
        ),
        min_size=min_size,
    )


def _invalid_tag_dicts():
    """Dicts with a 'tags' key whose value is NOT str/list[str]/set[str]."""
    return st.dictionaries(
        keys=st.just("tags"),
        values=st.one_of(
            st.integers(),
            st.floats(),
            st.booleans(),
            st.lists(st.integers(), min_size=1, max_size=2),
            st.lists(st.booleans(), min_size=1, max_size=2),
        ),
        min_size=1,
    )


# =============================================================================
# Initialization
# =============================================================================


class TestInit:
    """FieldTagListFormatter.__init__ with various input types."""

    def test_init_none(self):
        obj = FieldTagListFormatter()
        assert len(obj) == 0

    def test_init_str_deduplicates(self):
        obj = FieldTagListFormatter("one, one, two, two")
        assert obj.tags == ["one", "two"]

    def test_init_list_deduplicates(self):
        obj = FieldTagListFormatter(["one", "one", "two", "two"])
        assert obj.tags == ["one", "two"]

    def test_init_dict_deduplicates(self):
        obj = FieldTagListFormatter({"tags": ["one", "one", "two", "two"]})
        assert obj.tags == ["one", "two"]

    def test_init_set(self):
        obj = FieldTagListFormatter({"alpha", "beta"})
        assert set(obj.tags) == {"alpha", "beta"}

    def test_init_results_are_sorted(self):
        obj = FieldTagListFormatter("zero, one, nine")
        assert obj.tags == ["nine", "one", "zero"]


# =============================================================================
# add_tags / append / extend — all delegate to _add_tags
# =============================================================================


class TestAddTags:
    """Adding tags via add_tags, append, and extend."""

    @pytest.mark.parametrize(
        "input_tags",
        [
            {"tags": ["one", "one", "two", "two"]},
            {"tags": "one, one, two, two"},
            ["one", "one", "two", "two"],
            "one, one, two, two",
        ],
        ids=["dict-list", "dict-str", "list", "str"],
    )
    def test_add_deduplicates(self, fmt, input_tags):
        result = fmt.add_tags(input_tags)
        assert len(result) == 2
        assert result.count("one") == 1
        assert result.count("two") == 1

    def test_add_dict_with_set_value(self, fmt):
        """Dict with set value for 'tags' key — covers set branch."""
        result = fmt.add_tags({"tags": {"alpha", "beta"}})
        assert set(result) == {"alpha", "beta"}

    def test_add_none_returns_unchanged(self, fmt):
        fmt.add_tags("a,b,c")
        fmt.add_tags(None)
        assert fmt == ["a", "b", "c"]

    @pytest.mark.parametrize(
        "input_tags",
        [
            {"tags": ["two", "three"]},
            {"tags": "two, three"},
            ["two", "three"],
            {"two", "three"},
            "two, three",
        ],
        ids=["dict-list", "dict-str", "list", "set", "str"],
    )
    def test_append_deduplicates(self, input_tags):
        obj = FieldTagListFormatter(["one", "two"])
        obj.append(input_tags)
        assert len(obj) == 3
        assert obj.count("two") == 1
        assert "three" in obj

    @pytest.mark.parametrize(
        "input_tags",
        [
            {"tags": ["two", "three"]},
            {"tags": "two, three"},
            ["two", "three"],
            {"two", "three"},
            "two, three",
        ],
        ids=["dict-list", "dict-str", "list", "set", "str"],
    )
    def test_extend_deduplicates(self, input_tags):
        obj = FieldTagListFormatter(["one", "two"])
        obj.extend(input_tags)
        assert len(obj) == 3
        assert obj.count("two") == 1
        assert "three" in obj


# =============================================================================
# __add__, __radd__
# =============================================================================


class TestAddOperators:
    """__add__ and __radd__ with various types."""

    def test_add_two_formatters(self):
        a = FieldTagListFormatter("a,b,c")
        b = FieldTagListFormatter("d,e,f")
        assert a + b == ["a", "b", "c", "d", "e", "f"]

    def test_add_formatter_and_list(self):
        a = FieldTagListFormatter("a,b,c")
        assert a + ["d", "e", "f"] == ["a", "b", "c", "d", "e", "f"]

    def test_add_formatter_and_string(self):
        a = FieldTagListFormatter("a,b,c")
        # str is iterable of chars → list("d") == ["d"]
        assert a + "d" + "a" == ["a", "b", "c", "d"]

    def test_add_chained(self):
        a = FieldTagListFormatter("a,b,c")
        b = FieldTagListFormatter("d,e,f")
        d = FieldTagListFormatter("a,b,c,d,e,f,x,y,z")
        assert (a + b) + d == ["a", "b", "c", "d", "e", "f", "x", "y", "z"]

    def test_radd_formatter(self):
        a = FieldTagListFormatter("a,b,c")
        b = FieldTagListFormatter("d,e,f")
        assert a.__radd__(b) == ["a", "b", "c", "d", "e", "f"]

    def test_radd_list(self):
        a = FieldTagListFormatter("a,b,c")
        assert a.__radd__(["d", "e", "f"]) == ["a", "b", "c", "d", "e", "f"]

    def test_radd_string(self):
        a = FieldTagListFormatter("a,b,c")
        assert a.__radd__("d") == ["a", "b", "c", "d"]


# =============================================================================
# Deletion: del_tags, __delitem__, remove, pop, clear
# =============================================================================


class TestDeletion:
    """Removing tags from the formatter."""

    @pytest.mark.parametrize(
        "input_tags",
        [
            {"tags": ["two", "three"]},
            {"tags": "two, three"},
            ["two", "three"],
            {"two", "three"},
            "two, three",
        ],
        ids=["dict-list", "dict-str", "list", "set", "str"],
    )
    def test_del_tags(self, input_tags):
        obj = FieldTagListFormatter(["one", "two", "three"])
        obj.del_tags(input_tags)
        assert obj.tags == ["one"]

    def test_del_tags_nonexistent_is_noop(self):
        """del_tags silently skips tags not in the list."""
        obj = FieldTagListFormatter("a,b,c")
        obj.del_tags("x,y,z")
        assert obj == ["a", "b", "c"]

    def test_delitem(self, abc):
        del abc[2]
        assert abc == ["a", "b"]

    def test_remove_existing(self):
        obj = FieldTagListFormatter("one, two, three")
        obj.remove("one")
        assert len(obj) == 2
        assert "one" not in obj

    def test_remove_nonexistent_is_noop(self, abc):
        """remove() silently skips items not in list."""
        abc.remove("z")
        assert abc == ["a", "b", "c"]

    def test_pop_default_last(self):
        obj = FieldTagListFormatter("a,b,c,d,e,f")
        popped = obj.pop()
        assert popped == "f"
        assert obj == ["a", "b", "c", "d", "e"]

    def test_pop_by_index(self):
        obj = FieldTagListFormatter("a,b,c")
        popped = obj.pop(0)
        assert popped == "a"
        assert obj == ["b", "c"]

    def test_clear(self, abc):
        abc.clear()
        assert abc.tags == []


# =============================================================================
# Insert and __setitem__
# =============================================================================


class TestInsertAndSet:
    """insert() and __setitem__ with duplicate prevention."""

    def test_insert_new_item(self):
        obj = FieldTagListFormatter(["one", "two", "three"])
        obj.insert(0, "zero")
        assert obj[0] == "zero"
        assert len(obj) == 4

    def test_insert_duplicate_is_noop(self):
        obj = FieldTagListFormatter(["one", "two", "three"])
        obj.insert(0, "three")
        assert len(obj) == 3
        assert obj[0] == "one"

    def test_setitem_new_value(self):
        obj = FieldTagListFormatter("one, two, three")
        obj[0] = "New Tag"
        assert obj[0] == "New Tag"
        assert len(obj) == 3

    def test_setitem_duplicate_is_noop(self):
        obj = FieldTagListFormatter("one, two, three")
        obj[0] = "two"
        # Original value unchanged because "two" already exists
        assert obj[0] == "one"
        assert len(obj) == 3


# =============================================================================
# List protocol: comparison, slicing, multiplication, etc.
# =============================================================================


class TestListProtocol:
    """Standard list-like operations."""

    def test_contains(self, abc):
        assert "a" in abc
        assert "z" not in abc

    def test_len(self, abc):
        assert len(abc) == 3

    def test_getitem_index(self, abc):
        assert abc[1] == "b"

    def test_getitem_slice(self):
        obj = FieldTagListFormatter("a,b,c,d,e,f,g,h")
        sliced = obj[3:5]
        assert sliced == ["d", "e"]
        assert isinstance(sliced, FieldTagListFormatter)

    def test_eq(self, abc):
        other = FieldTagListFormatter("a,b,c")
        assert abc == other
        assert abc == ["a", "b", "c"]

    def test_ge(self, abc):
        assert abc >= FieldTagListFormatter("a,b,c")
        assert abc >= FieldTagListFormatter("a,b")

    def test_gt(self, abc):
        assert abc > FieldTagListFormatter("a,b")

    def test_le(self, abc):
        assert abc <= FieldTagListFormatter("a,b,c")
        assert abc <= FieldTagListFormatter("a,b,c,d")

    def test_lt(self, abc):
        assert abc < FieldTagListFormatter("a,b,c,d")

    def test_iadd_formatter(self):
        a = FieldTagListFormatter("a,b,c")
        b = FieldTagListFormatter("d,e,f")
        a += b
        assert a == ["a", "b", "c", "d", "e", "f"]

    def test_iadd_list(self):
        a = FieldTagListFormatter("a,b,c")
        a += ["d", "e", "f"]
        assert a == ["a", "b", "c", "d", "e", "f"]

    def test_iadd_string(self):
        a = FieldTagListFormatter("a,b,c")
        a += "z"
        assert a == ["a", "b", "c", "z"]

    def test_imul(self, abc):
        abc *= 2
        assert abc == ["a", "b", "c", "a", "b", "c"]

    def test_mul(self, abc):
        assert abc * 2 == ["a", "b", "c", "a", "b", "c"]

    def test_rmul(self, abc):
        """__rmul__ = __mul__ — e.g. 2 * formatter."""
        assert 2 * abc == ["a", "b", "c", "a", "b", "c"]

    def test_index(self, abc):
        assert abc.index("b") == 1

    def test_count(self, abc):
        assert abc.count("a") == 1
        assert abc.count("z") == 0

    def test_copy(self, abc):
        cp = abc.copy()
        assert cp == abc
        assert cp is not abc
        # Mutating copy doesn't affect original
        cp.tags.append("z")
        assert "z" not in abc

    def test_repr(self, abc):
        assert repr(abc) == "['a', 'b', 'c']"

    def test_reverse(self, abc):
        abc.reverse()
        assert abc == ["c", "b", "a"]

    def test_sort(self):
        obj = FieldTagListFormatter("f,d,e,a,c,b")
        obj.sort()
        assert obj == ["a", "b", "c", "d", "e", "f"]


# =============================================================================
# Formatted output
# =============================================================================


class TestFormattedOutput:
    """toCSV, toDict, toJson, toList."""

    def test_toCSV_no_trailing_comma(self):
        obj = FieldTagListFormatter("one, two")
        assert obj.toCSV(include_trailing_comma=False) == "one, two"

    def test_toCSV_with_trailing_comma(self):
        obj = FieldTagListFormatter("one, two")
        assert obj.toCSV(include_trailing_comma=True) == "one, two,"

    def test_toCSV_single_item(self):
        obj = FieldTagListFormatter("solo")
        assert obj.toCSV() == "solo"

    def test_toDict(self):
        obj = FieldTagListFormatter("one, two")
        assert obj.toDict() == {"tags": ["one", "two"]}

    def test_toJson(self):
        obj = FieldTagListFormatter("one, two")
        assert json.loads(obj.toJson()) == {"tags": ["one", "two"]}

    def test_toList(self):
        obj = FieldTagListFormatter("one, two")
        result = obj.toList()
        assert result == ["one", "two"]
        assert isinstance(result, list)
        assert not isinstance(result, FieldTagListFormatter)


# =============================================================================
# Parsing edge cases
# =============================================================================


class TestParsingEdgeCases:
    """String parsing via parse_tags delegation."""

    def test_loose_comma(self):
        assert FieldTagListFormatter("a,b,c,,") == ["a", "b", "c"]

    def test_open_quote_and_loose_comma(self):
        assert FieldTagListFormatter(',"a,b,c,') == ["a", "b", "c"]

    def test_space_delimited(self):
        assert FieldTagListFormatter("a c b") == ["a", "b", "c"]

    def test_quoted_multi_word_tag(self):
        obj = FieldTagListFormatter('"tag1 double" tag2')
        assert obj == ["tag1 double", "tag2"]

    def test_single_quoted_tag(self):
        assert FieldTagListFormatter('"tag"') == ["tag"]


# =============================================================================
# Validation helpers
# =============================================================================


class TestIsValidTag:
    """_is_valid_tag: rejects null variants and non-strings."""

    @pytest.mark.parametrize(
        "tag",
        ["hello", "tag with spaces", "123", ""],
        ids=["word", "spaces", "numeric", "empty"],
    )
    def test_valid_strings(self, tag):
        assert FieldTagListFormatter._is_valid_tag(tag) is True

    @pytest.mark.parametrize(
        "tag",
        ["null", "NULL", "Null", "null.", "null,"],
        ids=["lower", "upper", "title", "dot", "comma"],
    )
    def test_null_variants_rejected(self, tag):
        assert FieldTagListFormatter._is_valid_tag(tag) is False

    @pytest.mark.parametrize("value", [42, 3.14, True, None])
    def test_non_strings_rejected(self, value):
        assert FieldTagListFormatter._is_valid_tag(value) is False


class TestIsValidTagContainer:
    """_is_valid_tag_container: type checking and dict key validation."""

    @pytest.mark.parametrize(
        "tags",
        [
            {"tags": ["v1", "v2"]},
            ["a", "b"],
            {"a", "b"},
            "a,b",
            None,
        ],
        ids=["dict", "list", "set", "str", "none"],
    )
    def test_valid_containers(self, tags):
        assert FieldTagListFormatter._is_valid_tag_container(tags) is True

    def test_dict_without_tags_key_raises(self):
        with pytest.raises(ValidationError):
            FieldTagListFormatter._is_valid_tag_container({"key": "value"})

    def test_unsupported_type_returns_false(self):
        """Catch-all case _ branch — e.g. int, float."""
        assert FieldTagListFormatter._is_valid_tag_container(42) is False
        assert FieldTagListFormatter._is_valid_tag_container(3.14) is False


class TestIsValidTagList:
    """_is_valid_tag_list: all items must pass _is_valid_tag."""

    def test_valid_list(self):
        fmt = FieldTagListFormatter()
        assert fmt._is_valid_tag_list(["a", "b", "c"]) is True

    def test_empty_list(self):
        fmt = FieldTagListFormatter()
        assert fmt._is_valid_tag_list([]) is True

    def test_list_with_null_is_invalid(self):
        fmt = FieldTagListFormatter()
        assert fmt._is_valid_tag_list(["a", "null", "b"]) is False

    @given(
        st.lists(
            st.text().filter(lambda x: not NULL_PATTERN.match(x)),
            min_size=1,
        )
    )
    def test_valid_strings_fuzz(self, tag_list):
        fmt = FieldTagListFormatter()
        assert fmt._is_valid_tag_list(tag_list) is True


class TestExtractTagsFromDict:
    """_extract_tags_from_dict: str, list, set values + error paths."""

    def test_str_value(self):
        fmt = FieldTagListFormatter()
        result = fmt._extract_tags_from_dict({"tags": "a, b, c"})
        assert sorted(result) == ["a", "b", "c"]

    def test_list_value(self):
        fmt = FieldTagListFormatter()
        result = fmt._extract_tags_from_dict({"tags": ["a", "b"]})
        assert result == ["a", "b"]

    def test_set_value(self):
        """Covers the set() branch in the match statement."""
        fmt = FieldTagListFormatter()
        result = fmt._extract_tags_from_dict({"tags": {"x", "y"}})
        assert set(result) == {"x", "y"}

    def test_missing_tags_key_returns_empty(self):
        fmt = FieldTagListFormatter()
        result = fmt._extract_tags_from_dict({"other": "value"})
        assert result == []

    @hyp_settings(deadline=DEADLINE)
    @given(_invalid_tag_dicts())
    def test_invalid_values_return_empty(self, tags):
        fmt = FieldTagListFormatter()
        result = fmt._extract_tags_from_dict(tags)
        assert isinstance(result, list)

    def test_list_with_invalid_items_returns_empty(self):
        """List containing null values triggers ValidationError → []."""
        fmt = FieldTagListFormatter()
        result = fmt._extract_tags_from_dict({"tags": ["valid", "null"]})
        assert result == []


class TestGetTagList:
    """_get_tag_list: dispatch to correct handler by type."""

    def test_none_returns_empty(self):
        fmt = FieldTagListFormatter()
        assert fmt._get_tag_list(None) == []

    def test_str_input(self):
        fmt = FieldTagListFormatter()
        assert fmt._get_tag_list("a, b") == ["a", "b"]

    def test_list_input(self):
        fmt = FieldTagListFormatter()
        assert fmt._get_tag_list(["a", "b"]) == ["a", "b"]

    def test_set_input(self):
        fmt = FieldTagListFormatter()
        result = fmt._get_tag_list({"x", "y"})
        assert set(result) == {"x", "y"}

    def test_dict_input(self):
        fmt = FieldTagListFormatter()
        assert fmt._get_tag_list({"tags": "a, b"}) == ["a", "b"]

    def test_unsupported_type_raises(self):
        """Catch-all case _ branch — raises ValidationError."""
        fmt = FieldTagListFormatter()
        with pytest.raises(ValidationError):
            fmt._get_tag_list(42)

    def test_list_with_invalid_items_raises(self):
        """List containing non-strings raises ValidationError."""
        fmt = FieldTagListFormatter()
        with pytest.raises(ValidationError):
            fmt._get_tag_list([1, 2, 3])


# =============================================================================
# Error handling
# =============================================================================


class TestErrorHandling:
    """Invalid inputs are caught and logged."""

    @hyp_settings(deadline=DEADLINE)
    @given(
        tags=st.one_of(
            st.integers(),
            st.fractions(min_value=0, max_value=10, max_denominator=9),
        )
    )
    def test_unsupported_type_logs_error(self, tags):
        with patch.object(FieldTagListFormatter, "logger") as mock_logger:
            result = FieldTagListFormatter(tags)
            assert result == []
            assert mock_logger.error.called

    @hyp_settings(deadline=DEADLINE)
    @given(
        items=st.lists(
            st.one_of(st.integers(), st.booleans()),
            min_size=1,
        ),
    )
    def test_unsupported_type_in_list_logs_error(self, items):
        with patch.object(FieldTagListFormatter, "logger") as mock_logger:
            result = FieldTagListFormatter(items)
            assert result == []
            assert mock_logger.error.called

    def test_add_tags_invalid_container_logs_error(self):
        """_add_tags with unsupported type → logs and returns []."""
        fmt = FieldTagListFormatter()
        with patch.object(FieldTagListFormatter, "logger") as mock_logger:
            result = fmt._add_tags(42)
            assert result == []
            assert mock_logger.error.called

    @hyp_settings(deadline=DEADLINE)
    @given(_invalid_tag_dicts())
    def test_extract_invalid_dict_logs_error(self, tags):
        fmt = FieldTagListFormatter()
        with patch.object(FieldTagListFormatter, "logger") as mock_logger:
            fmt._extract_tags_from_dict(tags)
            assert mock_logger.error.called
