# tests/test_assets.py
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from django.test import TestCase
from tag_me.assets import get_tag_me_css, get_tag_me_js, _load_vite_manifest


class TestViteAssetLoading(TestCase):
    """Test Vite asset manifest loading."""

    def setUp(self):
        """Clear the manifest cache before each test."""
        _load_vite_manifest.cache_clear()

    def tearDown(self):
        """Clear the manifest cache after each test."""
        _load_vite_manifest.cache_clear()

    # ============================================
    # HAPPY PATH TESTS
    # ============================================

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_get_tag_me_js_success(self, mock_path, mock_find):
        """Test successful JS asset retrieval."""
        mock_manifest = {
            "src/tag-me.js": {
                "file": "js/tag-me.abc123.js",
            }
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        result = get_tag_me_js()

        self.assertEqual(result, "tag_me/dist/js/tag-me.abc123.js")
        mock_find.assert_called_once_with("tag_me/dist/manifest.json")

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_get_tag_me_css_success(self, mock_path, mock_find):
        """Test successful CSS asset retrieval."""
        mock_manifest = {
            "style.css": {
                "file": "css/tag-me.def456.css",
            }
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        result = get_tag_me_css()

        self.assertEqual(result, "tag_me/dist/css/tag-me.def456.css")
        mock_find.assert_called_once_with("tag_me/dist/manifest.json")

    # ============================================
    # ERROR PATH TESTS
    # ============================================

    @patch("tag_me.assets.finders.find")
    def test_manifest_not_found(self, mock_find):
        """Test FileNotFoundError when manifest is missing."""
        # Clear cache to ensure we hit the actual code path
        _load_vite_manifest.cache_clear()

        mock_find.return_value = None

        with self.assertRaises(FileNotFoundError) as context:
            get_tag_me_js()

        self.assertIn("Vite manifest not found", str(context.exception))
        self.assertIn("npm run prod", str(context.exception))

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_malformed_json_manifest(self, mock_path, mock_find):
        """Test ValueError when manifest contains invalid JSON."""
        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = "{ invalid json }"
        mock_path.return_value = mock_path_instance

        with self.assertRaises(ValueError) as context:
            get_tag_me_js()

        self.assertIn("Invalid JSON", str(context.exception))

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_js_entry_missing_in_manifest(self, mock_path, mock_find):
        """Test ValueError when JS entry is missing from manifest."""
        mock_manifest = {
            "style.css": {
                "file": "css/tag-me.def456.css",
            }
            # Missing "src/tag-me.js" entry
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        with self.assertRaises(ValueError) as context:
            get_tag_me_js()

        self.assertIn("JS entry 'src/tag-me.js' not found", str(context.exception))
        self.assertIn("Available keys:", str(context.exception))

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_css_entry_missing_in_manifest(self, mock_path, mock_find):
        """Test ValueError when CSS entry is missing from manifest."""
        mock_manifest = {
            "src/tag-me.js": {
                "file": "js/tag-me.abc123.js",
            }
            # Missing "style.css" entry
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        with self.assertRaises(ValueError) as context:
            get_tag_me_css()

        self.assertIn("CSS entry 'style.css' not found", str(context.exception))
        self.assertIn("Available keys:", str(context.exception))

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_js_entry_missing_file_key(self, mock_path, mock_find):
        """Test ValueError when JS entry exists but has no 'file' key."""
        mock_manifest = {
            "src/tag-me.js": {
                # Missing "file" key
                "name": "tag-me",
            }
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        with self.assertRaises(ValueError) as context:
            get_tag_me_js()

        self.assertIn("JS entry 'src/tag-me.js' not found", str(context.exception))

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_css_entry_missing_file_key(self, mock_path, mock_find):
        """Test ValueError when CSS entry exists but has no 'file' key."""
        mock_manifest = {
            "style.css": {
                # Missing "file" key
                "src": "style.css",
            }
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        with self.assertRaises(ValueError) as context:
            get_tag_me_css()

        self.assertIn("CSS entry 'style.css' not found", str(context.exception))

    # ============================================
    # CACHE BEHAVIOR TESTS
    # ============================================

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_manifest_caching(self, mock_path, mock_find):
        """Test that manifest is cached and disk I/O only happens once."""
        mock_manifest = {
            "src/tag-me.js": {
                "file": "js/tag-me.abc123.js",
            },
            "style.css": {
                "file": "css/tag-me.def456.css",
            },
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        # First call - should read from disk
        result1 = get_tag_me_js()
        self.assertEqual(mock_find.call_count, 1)
        self.assertEqual(mock_path_instance.read_text.call_count, 1)

        # Second call - should use cache (no additional disk I/O)
        result2 = get_tag_me_js()
        self.assertEqual(mock_find.call_count, 1)  # Still 1
        self.assertEqual(mock_path_instance.read_text.call_count, 1)  # Still 1

        # Third call for CSS - should still use same cached manifest
        result3 = get_tag_me_css()
        self.assertEqual(mock_find.call_count, 1)  # Still 1
        self.assertEqual(mock_path_instance.read_text.call_count, 1)  # Still 1

        # Verify results are correct
        self.assertEqual(result1, "tag_me/dist/js/tag-me.abc123.js")
        self.assertEqual(result2, "tag_me/dist/js/tag-me.abc123.js")
        self.assertEqual(result3, "tag_me/dist/css/tag-me.def456.css")

    @patch("tag_me.assets.finders.find")
    @patch("tag_me.assets.Path")
    def test_cache_clear(self, mock_path, mock_find):
        """Test that cache can be manually cleared."""
        mock_manifest = {
            "src/tag-me.js": {
                "file": "js/tag-me.abc123.js",
            }
        }

        mock_find.return_value = "/path/to/manifest.json"
        mock_path_instance = Mock()
        mock_path_instance.read_text.return_value = json.dumps(mock_manifest)
        mock_path.return_value = mock_path_instance

        # First call
        get_tag_me_js()
        self.assertEqual(mock_find.call_count, 1)

        # Clear cache
        _load_vite_manifest.cache_clear()

        # Second call - should read from disk again
        get_tag_me_js()
        self.assertEqual(mock_find.call_count, 2)


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
