# tag_me/assets.py (simplified)

import json
import logging
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders

logger = logging.getLogger(__name__)


class ViteManifestError(Exception):
    """Raised when there's an issue with the Vite manifest"""

    pass


@lru_cache(maxsize=1)
def _load_vite_manifest():
    """Load and cache the tag-me Vite manifest."""
    manifest_path = "tag_me/dist/manifest.json"
    manifest_path_str = finders.find(manifest_path)

    if not manifest_path_str:
        if settings.DEBUG:
            logger.warning(
                f"Vite manifest not found at {manifest_path}. "
                "Run 'npm run build' to generate assets."
            )
            return {}
        else:
            raise ViteManifestError(
                f"Vite manifest not found at {manifest_path}. "
                "Ensure assets were built before deployment."
            )

    manifest_file = Path(manifest_path_str)

    try:
        manifest = json.loads(manifest_file.read_text())
        logger.debug(f"Loaded tag-me manifest with {len(manifest)} entries")
        return manifest
    except json.JSONDecodeError as e:
        raise ViteManifestError(f"Invalid JSON in Vite manifest: {e}")


def get_tag_me_js():
    """Get the cache-busted JS file path from tag-me's Vite manifest."""
    manifest = _load_vite_manifest()

    if not manifest:
        fallback = "tag_me/dist/js/tag-me.js"
        logger.warning(f"No manifest found, using development fallback: {fallback}")
        return fallback

    js_key = "src/tag-me.js"

    if js_key not in manifest:
        available_keys = list(manifest.keys())
        raise ViteManifestError(
            f"JavaScript entry '{js_key}' not found in manifest. "
            f"Available keys: {available_keys}"
        )

    entry = manifest[js_key]
    file_path = entry.get("file")

    if not file_path:
        raise ViteManifestError(f"No 'file' key in JS entry: {entry}")

    return f"tag_me/dist/{file_path}"


def get_tag_me_css():
    """Get the cache-busted CSS file path from tag-me's Vite manifest."""
    manifest = _load_vite_manifest()

    if not manifest:
        fallback = "tag_me/dist/css/tag-me.css"
        logger.warning(f"No manifest found, using development fallback: {fallback}")
        return fallback

    css_key = "style.css"

    if css_key not in manifest:
        available_keys = list(manifest.keys())
        raise ViteManifestError(
            f"CSS entry '{css_key}' not found in manifest. "
            f"Available keys: {available_keys}"
        )

    entry = manifest[css_key]
    file_path = entry.get("file")

    if not file_path:
        raise ViteManifestError(f"No 'file' key in CSS entry: {entry}")

    return f"tag_me/dist/{file_path}"


def clear_manifest_cache():
    """Clear the cached manifest (useful for development)."""
    _load_vite_manifest.cache_clear()
    logger.info("Vite manifest cache cleared")
