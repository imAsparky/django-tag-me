# tag_me/assets.py

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


def _get_manifest_path():
    """
    Get the manifest path from settings or use tag-me's default.

    Returns:
        str: Path to manifest relative to STATIC_ROOT/staticfiles
    """
    # Check if project wants to use custom manifest (main project's CSS)
    custom_path = getattr(settings, "DJ_TAG_ME_CSS_MANIFEST_PATH", None)

    if custom_path:
        logger.debug(f"Using custom manifest path: {custom_path}")
        return custom_path

    # Default: use tag-me's own manifest
    default_path = "tag_me/dist/manifest.json"
    logger.debug(f"Using default tag-me manifest: {default_path}")
    return default_path


@lru_cache(maxsize=2)  # Cache both tag-me and project manifests if needed
def _load_vite_manifest(manifest_path=None):
    """
    Load and cache the Vite manifest.

    Args:
        manifest_path: Optional specific path to load (for flexibility)

    Returns:
        dict: The parsed manifest JSON, or empty dict if not found in DEBUG mode

    Raises:
        ViteManifestError: If manifest not found in production or invalid JSON
    """
    if manifest_path is None:
        manifest_path = _get_manifest_path()

    manifest_path_str = finders.find(manifest_path)

    if not manifest_path_str:
        # In development, manifest might not exist yet
        if settings.DEBUG:
            logger.warning(
                f"Vite manifest not found at {manifest_path}. "
                "Run your build command to generate assets."
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
        logger.debug(
            f"Loaded manifest from {manifest_path} with {len(manifest)} entries"
        )
        return manifest
    except json.JSONDecodeError as e:
        raise ViteManifestError(
            f"Invalid JSON in Vite manifest at {manifest_path}: {e}"
        )


def get_tag_me_js():
    """
    Get the cache-busted JS file path from Vite manifest.

    Note: JS always comes from tag-me's own manifest, not the project's.
    This is because tag-me's JavaScript is independent.

    Returns:
        str: Path to hashed JS file (e.g., 'tag_me/dist/js/tag-me.D-lm_TpE.js')
             Falls back to 'tag_me/dist/js/tag-me.js' in development

    Raises:
        ViteManifestError: If manifest not found in production or JS entry missing
    """
    # Always use tag-me's own manifest for JS
    manifest = _load_vite_manifest(manifest_path="tag_me/dist/manifest.json")

    # Development fallback
    if not manifest:
        fallback = "tag_me/dist/js/tag-me.js"
        logger.warning(f"No manifest found, using development fallback: {fallback}")
        return fallback

    # Look for the JS entry
    js_key = "src/tag-me.js"

    if js_key not in manifest:
        available_keys = list(manifest.keys())
        raise ViteManifestError(
            f"JavaScript entry '{js_key}' not found in tag-me manifest. "
            f"Available keys: {available_keys}. "
            f"Did you run 'npm run dev' or 'npm run prod' in tag-me?"
        )

    entry = manifest[js_key]
    file_path = entry.get("file")

    if not file_path:
        raise ViteManifestError(f"No 'file' key in JS entry. Entry contents: {entry}")

    return f"tag_me/dist/{file_path}"


def get_tag_me_css():
    """
    Get the cache-busted CSS file path from Vite manifest.

    This can read from either:
    1. Your main project's manifest (if DJ_TAG_ME_CSS_MANIFEST_PATH is set)
    2. Tag-me's own manifest (default)

    This allows tag-me to use your project's CSS file which includes
    both your classes and tm: prefixed classes.

    Returns:
        str: Path to hashed CSS file
             - If using project CSS: your project's CSS path
             - If using tag-me CSS: 'tag_me/dist/css/tag-me.ClosEdPI.css'
             - Development fallback: 'tag_me/dist/css/tag-me.css'

    Raises:
        ViteManifestError: If manifest not found in production or CSS not found
    """
    manifest_path = _get_manifest_path()
    manifest = _load_vite_manifest(manifest_path=manifest_path)

    # Development fallback
    if not manifest:
        # Check if using custom manifest
        if getattr(settings, "DJ_TAG_ME_CSS_MANIFEST_PATH", None):
            fallback = getattr(settings, "DJ_TAG_ME_CSS_FALLBACK", "css/styles.css")
            logger.warning(f"No manifest found, using project CSS fallback: {fallback}")
            return fallback
        else:
            fallback = "tag_me/dist/css/tag-me.css"
            logger.warning(f"No manifest found, using tag-me CSS fallback: {fallback}")
            return fallback

    # Look for the CSS entry (same key format as tag-me)
    css_key = getattr(settings, "DJ_TAG_ME_CSS_MANIFEST_KEY", "style.css")

    if css_key not in manifest:
        available_keys = list(manifest.keys())
        raise ViteManifestError(
            f"CSS entry '{css_key}' not found in manifest at {manifest_path}. "
            f"Available keys: {available_keys}. "
            f"Did you run your build command?"
        )

    entry = manifest[css_key]
    file_path = entry.get("file")

    if not file_path:
        raise ViteManifestError(f"No 'file' key in CSS entry. Entry contents: {entry}")

    # If using custom manifest, prepend the custom base path
    css_base_path = getattr(settings, "DJ_TAG_ME_CSS_BASE_PATH", "tag_me/dist")
    return f"{css_base_path}/{file_path}"


def clear_manifest_cache():
    """
    Clear the cached manifests (useful for development).

    Call this when you want to reload manifests without restarting the server.

    Example:
        from tag_me.assets import clear_manifest_cache
        clear_manifest_cache()
    """
    _load_vite_manifest.cache_clear()
    logger.info("Vite manifest cache cleared")


# Development helper
if settings.DEBUG:

    def debug_manifest():
        """Print manifest contents and resolved paths for debugging"""
        try:
            manifest_path = _get_manifest_path()
            print("\n" + "=" * 60)
            print("TAG-ME ASSET CONFIGURATION")
            print("=" * 60)
            print(f"Manifest Path: {manifest_path}")
            print(
                f"CSS Manifest Key: {getattr(settings, 'DJ_TAG_ME_CSS_MANIFEST_KEY', 'style.css')}"
            )
            print(
                f"CSS Base Path: {getattr(settings, 'DJ_TAG_ME_CSS_BASE_PATH', 'tag_me/dist')}"
            )

            manifest = _load_vite_manifest(manifest_path=manifest_path)
            if manifest:
                print("\n" + "=" * 60)
                print("MANIFEST CONTENTS")
                print("=" * 60)
                print(json.dumps(manifest, indent=2))

                print("\n" + "=" * 60)
                print("RESOLVED ASSET PATHS")
                print("=" * 60)

                try:
                    js_path = get_tag_me_js()
                    print(f"✅ JavaScript: {js_path}")
                except ViteManifestError as e:
                    print(f"❌ JavaScript: {e}")

                try:
                    css_path = get_tag_me_css()
                    print(f"✅ CSS:        {css_path}")
                except ViteManifestError as e:
                    print(f"❌ CSS:        {e}")

                print("=" * 60 + "\n")
            else:
                print("\n⚠️  No manifest found. Run your build command.\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
