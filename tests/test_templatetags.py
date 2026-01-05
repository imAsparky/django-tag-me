"""
Tests for coverage gaps in:
- tag_me/templatetags/tag_me.py (32% -> 100%)
- tag_me/models/models.py lines 265-286 (check_field_sync_list_lengths)
- tag_me/models/models.py lines 698-728 (UserTag.save sync logic)

Run with: pytest tests/test_coverage_gaps.py -v
"""

from django.contrib.auth import get_user_model
from django.utils.safestring import SafeString

from tag_me.templatetags.tag_me import tag_me_pills

User = get_user_model()


# =============================================================================
# TEMPLATE TAG TESTS - tag_me_pills filter
# =============================================================================


class TestTagMePillsFilter:
    """Tests for the tag_me_pills template filter."""

    def test_empty_value_returns_empty_string(self):
        """Empty or None value should return empty string."""
        assert tag_me_pills("") == ""
        assert tag_me_pills(None) == ""

    def test_single_tag_returns_single_pill(self):
        """Single tag should return one pill."""
        result = tag_me_pills("python")

        assert "python" in result
        assert "inline-flex" in result
        assert "rounded-full" in result
        assert result.count("<div") == 1

    def test_multiple_tags_returns_multiple_pills(self):
        """Multiple comma-separated tags should return multiple pills."""
        result = tag_me_pills("python, django, flask")

        assert "python" in result
        assert "django" in result
        assert "flask" in result
        assert result.count("<div") == 3

    def test_strips_whitespace(self):
        """Should strip whitespace from tags."""
        result = tag_me_pills("  python  ,  django  ")

        # Tags should be stripped (no leading/trailing spaces in output)
        assert ">python<" in result
        assert ">django<" in result

    def test_filters_empty_items(self):
        """Should filter out empty items from trailing commas."""
        result = tag_me_pills("python,django,")

        assert "python" in result
        assert "django" in result
        # Should only have 2 pills, not 3 (empty string filtered)
        assert result.count("<div") == 2

    def test_unicode_escape_decoding(self):
        """Should decode Unicode escape sequences."""
        # \u0026 is &
        result = tag_me_pills("rock\\u0026roll")

        assert "rock&roll" in result

    def test_returns_marked_safe(self):
        """Should return a SafeString (mark_safe)."""

        result = tag_me_pills("python")

        assert isinstance(result, SafeString)

    def test_pill_styling_classes(self):
        """Should include expected Tailwind classes."""
        result = tag_me_pills("test")

        # Check key styling classes
        assert "text-indigo-800" in result
        assert "bg-indigo-50" in result
        assert "border-indigo-200" in result
        assert "shadow-sm" in result
