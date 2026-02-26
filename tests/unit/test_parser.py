"""
Tests for tag_me/utils/parser.py

Covers:
    - is_valid_char: alphanumeric, whitespace, quotes, commas, control chars
    - remove_control_chars: stripping from strings
    - split_strip: splitting with default/custom delimiters
    - _parse_tags / parse_tags: space-delimited, comma-delimited, quoted,
      unclosed quotes, complex cases, empty/whitespace input
    - edit_string_for_tags / _edit_string_for_tags: formatting tag objects
    - get_func: settings lookup with fallback
    - Control char injection: Hypothesis property tests

No database required.

Run with: pytest tests/test_parser.py -v
"""

import unicodedata
from types import SimpleNamespace

import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from tag_me.utils.parser import (
    _edit_string_for_tags,
    edit_string_for_tags,
    get_func,
    is_valid_char,
    parse_tags,
    remove_control_chars,
    split_strip,
)

# =============================================================================
# is_valid_char
# =============================================================================


class TestIsValidChar:
    """Test character validation for tag content."""

    @pytest.mark.parametrize("char", list("abcABC012"))
    def test_alphanumeric_allowed(self, char):
        assert is_valid_char(char) is True

    def test_space_allowed(self):
        assert is_valid_char(" ") is True

    def test_comma_allowed(self):
        assert is_valid_char(",") is True

    def test_double_quote_allowed(self):
        assert is_valid_char('"') is True

    def test_single_quote_allowed(self):
        assert is_valid_char("'") is True

    @pytest.mark.parametrize(
        "char",
        ["\t", "\n", "\x0b", "\x0c"],
        ids=["tab", "newline", "vtab", "formfeed"],
    )
    def test_whitespace_control_chars_rejected(self, char):
        assert is_valid_char(char) is False

    @pytest.mark.parametrize(
        "char",
        ["\x00", "\x01", "\x1f"],
        ids=["null", "soh", "us"],
    )
    def test_device_control_chars_rejected(self, char):
        assert is_valid_char(char) is False

    @pytest.mark.parametrize(
        "char",
        ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e"],
        ids=["LRE", "RLE", "PDF", "LRO", "RLO"],
    )
    def test_bidi_control_chars_rejected(self, char):
        assert is_valid_char(char) is False

    def test_pua_chars_rejected(self):
        assert is_valid_char("\ue000") is False

    @pytest.mark.parametrize("char", list("!@#$%^&*()-_=+[]{}|;:.<>?/~`"))
    def test_punctuation_generally_allowed(self, char):
        """Most punctuation passes the unicode category check."""
        # Some may be filtered by category; test they don't crash
        result = is_valid_char(char)
        assert isinstance(result, bool)

    def test_emoji_allowed(self):
        assert is_valid_char("\U0001f600") is True

    def test_accented_char_allowed(self):
        assert is_valid_char("\u00e9") is True  # é


# =============================================================================
# remove_control_chars
# =============================================================================


class TestRemoveControlChars:
    """Test stripping control characters from strings."""

    def test_clean_string_unchanged(self):
        assert remove_control_chars("hello world") == "hello world"

    def test_tab_removed(self):
        assert remove_control_chars("hello\tworld") == "helloworld"

    def test_newline_removed(self):
        assert remove_control_chars("hello\nworld") == "helloworld"

    def test_null_char_removed(self):
        assert remove_control_chars("hello\x00world") == "helloworld"

    def test_mixed_control_chars_removed(self):
        result = remove_control_chars("a\tb\nc\x00d\x0be")
        assert result == "abcde"

    def test_empty_string(self):
        assert remove_control_chars("") == ""

    def test_preserves_commas_and_quotes(self):
        assert remove_control_chars('"hello, world"') == '"hello, world"'

    def test_preserves_unicode(self):
        assert remove_control_chars("café \U0001f600") == "café \U0001f600"


# =============================================================================
# split_strip
# =============================================================================


class TestSplitStrip:
    """Test string splitting with whitespace stripping."""

    def test_empty_string(self):
        assert split_strip("") == []

    def test_comma_delimited(self):
        assert split_strip("a, b, c") == ["a", "b", "c"]

    def test_strips_whitespace(self):
        assert split_strip("  x  ,  y  ,  z  ") == ["x", "y", "z"]

    def test_filters_empty_segments(self):
        assert split_strip("a,,b,  ,c") == ["a", "b", "c"]

    def test_custom_delimiter(self):
        assert split_strip("a | b | c", "|") == ["a", "b", "c"]

    def test_space_delimiter(self):
        assert split_strip("apple ball cat", " ") == ["apple", "ball", "cat"]

    def test_trailing_delimiter(self):
        assert split_strip("a,b,c,") == ["a", "b", "c"]


# =============================================================================
# _parse_tags / parse_tags
# =============================================================================


class TestParseTags:
    """Test tag parsing with various delimiters and quoting styles."""

    def test_empty_string(self):
        assert parse_tags("") == []

    def test_whitespace_only(self):
        assert parse_tags(" ") == []

    def test_single_quote_only(self):
        assert parse_tags('"') == []

    def test_space_delimited(self):
        assert parse_tags("apple ball cat") == ["apple", "ball", "cat"]

    def test_comma_delimited(self):
        assert parse_tags("apple, ball cat") == ["apple", "ball cat"]

    def test_quoted_tag_with_comma(self):
        assert parse_tags('"apple, ball" cat dog') == [
            "apple, ball",
            "cat",
            "dog",
        ]

    def test_unquoted_comma_with_quoted_tag(self):
        assert parse_tags('"apple, ball", cat dog') == [
            "apple, ball",
            "cat dog",
        ]

    def test_quoted_multi_word(self):
        assert parse_tags('apple "ball cat" dog') == [
            "apple",
            "ball cat",
            "dog",
        ]

    def test_unclosed_double_quote(self):
        assert parse_tags('"apple" "ball dog') == ["apple", "ball", "dog"]

    def test_single_quotes_not_special(self):
        """Single quotes are treated as literal characters, not delimiters."""
        assert parse_tags("'apple, ball', cat dog") == [
            "'apple",
            "ball'",
            "cat dog",
        ]

    def test_complex_mixed_tags(self):
        tag_string = (
            '"Word with spaces", one, "two, with comma", "three ""quotes""", last'
        )
        expected = [
            "Word with spaces",
            "last",
            "one",
            "quotes",
            "three",
            "two, with comma",
        ]
        assert parse_tags(tag_string) == expected

    def test_result_sorted(self):
        result = parse_tags("cherry, apple, banana")
        assert result == sorted(result)

    def test_result_deduplicated(self):
        result = parse_tags("dup, dup, dup")
        assert result == ["dup"]


# =============================================================================
# edit_string_for_tags / _edit_string_for_tags
# =============================================================================


class TestEditStringForTags:
    """Test formatting tag objects into editable strings.

    Uses SimpleNamespace stubs — no DB required.
    """

    @staticmethod
    def _tag(tags_str):
        return SimpleNamespace(tags=tags_str)

    def test_empty_list(self):
        assert _edit_string_for_tags([]) == ""

    def test_simple_tags(self):
        tags = [self._tag("alpha"), self._tag("beta")]
        result = _edit_string_for_tags(tags)

        assert result == "alpha, beta"

    def test_tag_with_comma_quoted(self):
        tags = [self._tag("tag,2")]
        result = _edit_string_for_tags(tags)

        assert result == '"tag,2"'

    def test_tag_with_space_quoted(self):
        tags = [self._tag("tag 3")]
        result = _edit_string_for_tags(tags)

        assert result == '"tag 3"'

    def test_mixed_tags_sorted(self):
        tags = [
            self._tag("tag1"),
            self._tag("tag,2"),
            self._tag("tag 3"),
        ]
        result = _edit_string_for_tags(tags)

        assert result == '"tag 3", "tag,2", tag1'

    def test_edit_string_for_tags_delegates(self):
        """Public function delegates to private implementation."""
        tags = [self._tag("hello")]
        assert edit_string_for_tags(tags) == _edit_string_for_tags(tags)


# =============================================================================
# get_func
# =============================================================================


class TestGetFunc:
    """Test settings-based function resolution."""

    def test_returns_default_when_setting_missing(self):
        def my_default():
            return "default"

        func = get_func("NONEXISTENT_SETTING", my_default)
        assert func is my_default

    def test_returns_default_when_key_empty(self):
        sentinel = object()
        func = get_func("", sentinel)
        assert func is sentinel

    def test_returns_default_when_no_key(self):
        sentinel = object()
        func = get_func(default=sentinel)
        assert func is sentinel


# =============================================================================
# Control Character Injection (Hypothesis property tests)
# =============================================================================


def _is_control_char(char):
    """Check if a character is in a Unicode control category."""
    return unicodedata.category(char) in ["Cc", "Cf", "Cs", "Co", "Cn"]


# Strategy: a single control character
_control_char = st.characters().filter(_is_control_char)

# Strategy: a small list of positions and control chars for injection
_injections = st.lists(
    st.tuples(
        st.integers(min_value=0, max_value=50),  # position (clamped later)
        _control_char,
    ),
    min_size=0,
    max_size=3,
)


def _inject_chars(base_string, injections):
    """Deterministically inject control chars at given positions."""
    result = base_string
    for pos, char in injections:
        idx = min(pos, len(result))
        result = result[:idx] + char + result[idx:]
    return result


class TestControlCharInjection:
    """Hypothesis tests: parse_tags strips control chars from input.

    Each test injects random control characters into a known tag string
    and verifies the parse result is unchanged.
    """

    @hyp_settings(max_examples=50)
    @given(injections=_injections)
    def test_space_delimited(self, injections):
        modified = _inject_chars("apple ball cat", injections)
        assert parse_tags(modified) == ["apple", "ball", "cat"]

    @hyp_settings(max_examples=50)
    @given(injections=_injections)
    def test_comma_delimited(self, injections):
        modified = _inject_chars("apple, ball cat", injections)
        assert parse_tags(modified) == ["apple", "ball cat"]

    @hyp_settings(max_examples=50)
    @given(injections=_injections)
    def test_quoted_with_comma(self, injections):
        modified = _inject_chars('"apple, ball" cat dog', injections)
        assert parse_tags(modified) == ["apple, ball", "cat", "dog"]

    @hyp_settings(max_examples=50)
    @given(injections=_injections)
    def test_unquoted_comma(self, injections):
        modified = _inject_chars('"apple, ball", cat dog', injections)
        assert parse_tags(modified) == ["apple, ball", "cat dog"]

    @hyp_settings(max_examples=50)
    @given(injections=_injections)
    def test_space_delimited_quoted(self, injections):
        modified = _inject_chars('apple "ball cat" dog', injections)
        assert parse_tags(modified) == ["apple", "ball cat", "dog"]

    @hyp_settings(max_examples=50)
    @given(injections=_injections)
    def test_unclosed_quote(self, injections):
        modified = _inject_chars('"apple" "ball dog', injections)
        assert parse_tags(modified) == ["apple", "ball", "dog"]
