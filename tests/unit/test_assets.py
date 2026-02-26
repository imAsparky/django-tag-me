"""
Tests for tag_me.assets and tag_me.templatetags.tag_me_assets.

Covers:
    - _load_vite_manifest: happy path, caching, DEBUG fallback, missing file,
      malformed JSON
    - get_tag_me_js / get_tag_me_css: manifest lookup, missing entry, missing
      'file' key, empty-manifest fallback
    - clear_manifest_cache: utility wrapper
    - Template tags: tag_me_js, tag_me_css, tag_me_assets (combined HTML output)

Run with: pytest tests/test_assets.py -v
"""

import json
from unittest.mock import patch

import pytest
from django.template import Context, Template
from django.test import override_settings

from tag_me.assets import (
    ViteManifestError,
    _load_vite_manifest,
    clear_manifest_cache,
    get_tag_me_css,
    get_tag_me_js,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_MANIFEST = {
    "src/tag-me.js": {"file": "js/tag-me.abc123.js"},
    "style.css": {"file": "css/tag-me.def456.css"},
}


@pytest.fixture(autouse=True)
def _clear_manifest_cache():
    """Ensure every test starts and ends with a cold cache."""
    _load_vite_manifest.cache_clear()
    yield
    _load_vite_manifest.cache_clear()


def _patch_manifest(manifest_dict):
    """Return stacked patches that make _load_vite_manifest read *manifest_dict*.

    Patches ``finders.find`` (returns a truthy path) and
    ``Path.read_text`` on the instance returned by ``Path(path_str)``,
    avoiding a module-level replacement of the entire ``Path`` class.
    """
    json_text = json.dumps(manifest_dict)
    return (
        patch("tag_me.assets.finders.find", return_value="/fake/manifest.json"),
        patch(
            "tag_me.assets.Path",
            **{
                "return_value.read_text.return_value": json_text,
            },
        ),
    )


# =============================================================================
# _load_vite_manifest
# =============================================================================


class TestLoadViteManifest:
    """Low-level manifest loader: file I/O, error handling, caching."""

    def test_loads_manifest_from_disk(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            result = _load_vite_manifest()

        assert result == FULL_MANIFEST

    def test_caches_across_calls(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find as mock_find, p_path as mock_path:
            _load_vite_manifest()
            _load_vite_manifest()

            assert mock_find.call_count == 1
            assert mock_path.return_value.read_text.call_count == 1

    def test_cache_clear_forces_reload(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find as mock_find, p_path:
            _load_vite_manifest()
            _load_vite_manifest.cache_clear()
            _load_vite_manifest()

            assert mock_find.call_count == 2

    @override_settings(DEBUG=False)
    def test_raises_when_manifest_missing_production(self):
        with patch("tag_me.assets.finders.find", return_value=None):
            with pytest.raises(ViteManifestError, match="Vite manifest not found"):
                _load_vite_manifest()

    @override_settings(DEBUG=True)
    def test_returns_empty_dict_when_manifest_missing_debug(self):
        """DEBUG=True branch: log warning and return {} instead of raising."""
        with patch("tag_me.assets.finders.find", return_value=None):
            result = _load_vite_manifest()

        assert result == {}

    def test_raises_on_malformed_json(self):
        with (
            patch("tag_me.assets.finders.find", return_value="/fake/manifest.json"),
            patch(
                "tag_me.assets.Path",
                **{
                    "return_value.read_text.return_value": "{ not json }",
                },
            ),
        ):
            with pytest.raises(ViteManifestError, match="Invalid JSON"):
                _load_vite_manifest()


# =============================================================================
# get_tag_me_js
# =============================================================================


class TestGetTagMeJs:
    """JS asset path resolution from manifest."""

    def test_returns_prefixed_path(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            assert get_tag_me_js() == "tag_me/dist/js/tag-me.abc123.js"

    def test_raises_when_js_entry_missing(self):
        manifest = {"style.css": {"file": "css/tag-me.def456.css"}}
        p_find, p_path = _patch_manifest(manifest)
        with p_find, p_path:
            with pytest.raises(ViteManifestError, match="src/tag-me.js"):
                get_tag_me_js()

    def test_error_lists_available_keys(self):
        manifest = {"other.js": {"file": "other.js"}}
        p_find, p_path = _patch_manifest(manifest)
        with p_find, p_path:
            with pytest.raises(ViteManifestError, match="other.js"):
                get_tag_me_js()

    def test_raises_when_file_key_missing(self):
        manifest = {"src/tag-me.js": {"name": "tag-me"}}
        p_find, p_path = _patch_manifest(manifest)
        with p_find, p_path:
            with pytest.raises(ViteManifestError, match="No 'file' key"):
                get_tag_me_js()

    @override_settings(DEBUG=True)
    def test_fallback_when_manifest_empty(self):
        """Empty manifest (DEBUG=True, file missing) → development fallback."""
        with patch("tag_me.assets.finders.find", return_value=None):
            result = get_tag_me_js()

        assert result == "tag_me/dist/js/tag-me.js"


# =============================================================================
# get_tag_me_css
# =============================================================================


class TestGetTagMeCss:
    """CSS asset path resolution from manifest."""

    def test_returns_prefixed_path(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            assert get_tag_me_css() == "tag_me/dist/css/tag-me.def456.css"

    def test_raises_when_css_entry_missing(self):
        manifest = {"src/tag-me.js": {"file": "js/tag-me.abc123.js"}}
        p_find, p_path = _patch_manifest(manifest)
        with p_find, p_path:
            with pytest.raises(ViteManifestError, match="style.css"):
                get_tag_me_css()

    def test_raises_when_file_key_missing(self):
        manifest = {"style.css": {"src": "style.css"}}
        p_find, p_path = _patch_manifest(manifest)
        with p_find, p_path:
            with pytest.raises(ViteManifestError, match="No 'file' key"):
                get_tag_me_css()

    @override_settings(DEBUG=True)
    def test_fallback_when_manifest_empty(self):
        """Empty manifest (DEBUG=True, file missing) → development fallback."""
        with patch("tag_me.assets.finders.find", return_value=None):
            result = get_tag_me_css()

        assert result == "tag_me/dist/css/tag-me.css"


# =============================================================================
# clear_manifest_cache
# =============================================================================


class TestClearManifestCache:
    """Utility function that wraps cache_clear + logs."""

    def test_clears_cache(self):
        """After clear_manifest_cache(), next call re-reads from disk."""
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find as mock_find, p_path:
            _load_vite_manifest()
            assert mock_find.call_count == 1

            clear_manifest_cache()

            _load_vite_manifest()
            assert mock_find.call_count == 2

    def test_logs_info(self):
        with patch("tag_me.assets.logger") as mock_logger:
            clear_manifest_cache()

        mock_logger.info.assert_called_once()


# =============================================================================
# Template tags
# =============================================================================


class TestTemplateTags:
    """Template tags: tag_me_js, tag_me_css, tag_me_assets.

    Patches the manifest so tests don't depend on real built assets.
    """

    def test_tag_me_js_renders_static_url(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            template = Template("{% load tag_me_assets %}{% tag_me_js %}")
            rendered = template.render(Context({}))

        assert "js/tag-me.abc123.js" in rendered

    def test_tag_me_css_renders_static_url(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            template = Template("{% load tag_me_assets %}{% tag_me_css %}")
            rendered = template.render(Context({}))

        assert "css/tag-me.def456.css" in rendered

    def test_tag_me_assets_renders_both_tags(self):
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            template = Template("{% load tag_me_assets %}{% tag_me_assets %}")
            rendered = template.render(Context({}))

        assert '<link rel="stylesheet"' in rendered
        assert "css/tag-me.def456.css" in rendered
        assert "<script defer" in rendered
        assert "js/tag-me.abc123.js" in rendered

    def test_tag_me_assets_script_uses_defer(self):
        """Script tag must use defer, not type=module."""
        p_find, p_path = _patch_manifest(FULL_MANIFEST)
        with p_find, p_path:
            template = Template("{% load tag_me_assets %}{% tag_me_assets %}")
            rendered = template.render(Context({}))

        assert 'type="module"' not in rendered
        assert "defer" in rendered
