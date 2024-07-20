"""tag parsing tests"""

import random
import unicodedata

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

#
from tag_me.models import UserTag
from tag_me.utils.parser import edit_string_for_tags, parse_tags, split_strip

#
User = get_user_model()


def is_control_char(char):
    category = unicodedata.category(char)
    return category in ["Cc", "Cf", "Cs", "Co", "Cn"]


class TestTagStringParser(SimpleTestCase):
    """These tests cover what isnt hit with test_collections.py"""

    def test_empty_string(self):
        tags = parse_tags("")

        assert tags == []

    def test_split_strip_empty(self):
        tags = split_strip("")

        assert tags == []


class TestTagsStringEdit(TestCase):
    """
    Tests the transformation of a tag list into a correctly formatted string
    for storage or display.
    """

    def test_edit_string(self):
        user = User.objects.create(
            username="User1",
            password="pass",
            email="user1@email.com",
        )
        assert user.username == "User1"
        tag1 = UserTag.objects.create(tags="tag1")
        tag2 = UserTag.objects.create(tags="tag,2")
        tag3 = UserTag.objects.create(tags="tag 3")

        tag_list = [
            tag1,
            tag2,
            tag3,
        ]

        assert edit_string_for_tags(tag_list) == '"tag 3", "tag,2", tag1'


class TestBasicTagParsing(TestCase):
    """
    Tests the core functionality of the tag parsing logic, including various
    delimiter scenarios and quoting styles.
    """

    def test_no_commas_space_delimited(self):
        tag_string = "apple ball cat"
        expected_tags = ["apple", "ball", "cat"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    def test_comma_delimited(self):
        tag_string = "apple, ball cat"
        expected_tags = ["apple", "ball cat"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    def test_all_commas_quoted(self):
        tag_string = '"apple, ball" cat dog'
        expected_tags = ["apple, ball", "cat", "dog"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    def test_single_quotes(self):
        tag_string = "'apple, ball', cat dog"
        expected_tags = ["'apple", "ball'", "cat dog"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    def test_space_delimited(self):
        tag_string = 'apple "ball cat" dog'
        expected_tags = ["apple", "ball cat", "dog"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    def test_unclosed_double_quote(self):
        tag_string = '"apple" "ball dog'
        expected_tags = ["apple", "ball", "dog"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    # @given(st.text(min_size=1))
    # def test_unquoted_commas_as_delimiter(self, tag_string):
    #     """
    #     Modify tag_string to introduce an unquoted comma, perhaps using
    #     string substitution.
    #     """
    #     modified_tag_string = tag_string.replace(" ", ", ", 1)
    #
    #     result = parse_tags(modified_tag_string)
    #
    #     # Assert that the tags were split using the comma
    #     if "," in modified_tag_string:
    #         assert len(result) > 1  # Expect splitting behavior
    # else:
    #     assert (
    #         len(result) == 1
    #     )  # Expect a single tag since no commas are present

    def test_complex_list_ofTags(self):
        tag_string = '"Word with spaces", one, "two, with comma", "three ""quotes""", last'
        expected_tags = [
            "Word with spaces",
            "last",
            "one",
            "quotes",
            "three",
            "two, with comma",
        ]

        result = parse_tags(tag_string)
        assert result == expected_tags

    def test_empty_tag_with_single_space(self):
        result = parse_tags(" ")
        assert len(result) == 0

    def test_empty_tag_with_double_quote(self):
        result = parse_tags('"')
        assert len(result) == 0


class TestRemoveControlChars(TestCase):
    """Tests the control character removal logic under various tag parsing scenarios.

    Uses Hypothesis to inject random control characters into diverse test strings.

    Excluded Characters:
        * Bidirectional formatting (e.g., for mixed right-to-left and left-to-right text)
        * Legacy device control characters
        * Information separators
        * "Next Line", carriage return, and other control characters
        * Private Use Area (PUA) Unicode blocks
        * Standard whitespace (newline, tab, etc.)

    Edge Cases Tested:
        * Invisible formatting that could disrupt parsing
        * Unexpected behavior with bidirectional text
        * Compatibility issues with legacy devices
        * Data integrity problems if separators are used as delimiters
        * Potential issues with user-defined characters in PUAs
    """

    control_chars = st.characters().filter(lambda char: is_control_char(char))

    @given(control_chars)
    def test_no_commas_space_delimited(self, control_char):
        tag_string = "apple ball cat"  # Explicit tag string

        num_insertions = random.randint(0, 3)
        modified_tag_string = tag_string
        for _ in range(num_insertions):
            insert_index = random.randint(0, len(modified_tag_string) - 1)
            modified_tag_string = (
                modified_tag_string[:insert_index]
                + control_char
                + modified_tag_string[insert_index:]
            )

        expected_tags = ["apple", "ball", "cat"]
        result = parse_tags(modified_tag_string)
        assert result == expected_tags

    @given(control_chars)
    def test_comma_delimited(self, control_char):
        tag_string = "apple, ball cat"

        num_insertions = random.randint(0, 3)
        modified_tag_string = tag_string
        for _ in range(num_insertions):
            insert_index = random.randint(0, len(modified_tag_string) - 1)
            modified_tag_string = (
                modified_tag_string[:insert_index]
                + control_char
                + modified_tag_string[insert_index:]
            )

        expected_tags = ["apple", "ball cat"]
        result = parse_tags(tag_string)
        assert result == expected_tags

    @given(control_chars)
    def test_all_commas_quoted(self, control_char):
        tag_string = '"apple, ball" cat dog'
        num_insertions = random.randint(0, 3)
        modified_tag_string = tag_string
        for _ in range(num_insertions):
            insert_index = random.randint(0, len(modified_tag_string) - 1)
            modified_tag_string = (
                modified_tag_string[:insert_index]
                + control_char
                + modified_tag_string[insert_index:]
            )

        expected_tags = ["apple, ball", "cat", "dog"]
        result = parse_tags(modified_tag_string)
        assert result == expected_tags

    @given(control_chars)
    def test_unquoted_comma(self, control_char):
        tag_string = '"apple, ball", cat dog'
        num_insertions = random.randint(0, 3)
        modified_tag_string = tag_string
        for _ in range(num_insertions):
            insert_index = random.randint(0, len(modified_tag_string) - 1)
            modified_tag_string = (
                modified_tag_string[:insert_index]
                + control_char
                + modified_tag_string[insert_index:]
            )

        expected_tags = ["apple, ball", "cat dog"]
        result = parse_tags(modified_tag_string)
        assert result == expected_tags

    @given(control_chars)
    def test_space_delimited(self, control_char):
        tag_string = 'apple "ball cat" dog'
        num_insertions = random.randint(0, 3)
        modified_tag_string = tag_string
        for _ in range(num_insertions):
            insert_index = random.randint(0, len(modified_tag_string) - 1)
            modified_tag_string = (
                modified_tag_string[:insert_index]
                + control_char
                + modified_tag_string[insert_index:]
            )

        expected_tags = ["apple", "ball cat", "dog"]
        result = parse_tags(modified_tag_string)
        assert result == expected_tags

    @given(
        control_chars,
    )
    def test_unclosed_double_quote(self, control_char):
        """
        Tests the control character removal logic under various tag parsing
        scenarios.

        Uses Hypothesis to inject random control characters into diverse test
        strings.
        """
        tag_string = '"apple" "ball dog'

        num_insertions = random.randint(
            0, 3
        )  # Number of control chars to insert

        modified_tag_string = tag_string  # Start with a copy of the original
        for _ in range(num_insertions):
            insert_index = random.randint(0, len(modified_tag_string) - 1)
            modified_tag_string = (
                modified_tag_string[:insert_index]
                + control_char
                + modified_tag_string[insert_index:]
            )

        expected_tags = ["apple", "ball", "dog"]  # Assuming correct parsing
        result = parse_tags(modified_tag_string)
        assert result == expected_tags
