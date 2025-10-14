# tests/test_assets.py

import json
from unittest.mock import Mock, patch

from django.test import TestCase

from tag_me.assets import get_tag_me_css, get_tag_me_js, get_vite_asset


class TestViteAssetLoading(TestCase):
    """Test Vite asset manifest loading."""

    def test_get_tag_me_js(self):
        """Test JS asset retrieval."""
        js_path = get_tag_me_js()
        self.assertIn("tag_me/dist/", js_path)
        self.assertTrue(js_path.endswith(".js"))

    def test_get_tag_me_css(self):
        """Test CSS asset retrieval."""
        css_path = get_tag_me_css()
        self.assertIn("tag_me/dist/", css_path)
        self.assertTrue(css_path.endswith(".css"))

    @patch("tag_me.assets.finders.find")
    def test_fallback_when_manifest_not_found(self, mock_find):
        """Test fallback to unhashed names when manifest missing."""
        mock_find.return_value = None

        result = get_vite_asset("tag-me.js")
        self.assertEqual(result, "tag_me/dist/tag-me.js")

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_manifest_parsing(self, mock_path, mock_find):
        """Test manifest JSON parsing."""
        # Mock manifest content
        mock_manifest = {
            "src/tag-me.js": {
                "file": "js/tag-me.abc123.js",
                "css": ["css/tag-me.def456.css"],
            }
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        result = get_vite_asset("src/tag-me.js")
        self.assertEqual(result, "tag_me/dist/js/tag-me.abc123.js")


class TestTemplateTags(TestCase):
    """Test template tag rendering."""

    def test_tag_me_assets_tag(self):
        """Test combined assets template tag."""
        from django.template import Context, Template

        template = Template("{% load tag_me_assets %}{% tag_me_assets %}")
        rendered = template.render(Context({}))

        self.assertIn('<link rel="stylesheet"', rendered)
        self.assertIn("<script src=", rendered)
        self.assertIn("tag_me/dist/", rendered)
