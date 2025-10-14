# tag_me/assets.py

import json
import logging
from pathlib import Path

from django.contrib.staticfiles import finders

logger = logging.getLogger(__name__)


def get_vite_asset(asset_name):
    """
    Get the actual filename of a Vite asset from the manifest.
    Handles hashed filenames for cache busting.

    Args:
        asset_name (str): The original asset name (e.g., 'tag-me.js', 'tag-me.css')

    Returns:
        str: The actual filename with hash (e.g., 'js/tag-me.abc123.js')

    Examples:
        >>> get_vite_asset('src/tag-me.js')
        'tag_me/dist/js/tag-me.a1b2c3d4.js'

        >>> get_vite_asset('tag-me.css')
        'tag_me/dist/css/tag-me.e5f6g7h8.css'
    """
    try:
        # Find the manifest file
        manifest_path_str = finders.find("tag_me/dist/.vite/manifest.json")

        if not manifest_path_str:
            # Fallback to original filename if no manifest
            logger.warning(
                f"Vite manifest not found for {asset_name}, using fallback path"
            )
            return f"tag_me/dist/{asset_name}"

        # Read the manifest
        manifest_path = Path(manifest_path_str)
        manifest = json.loads(manifest_path.read_text())

        # Handle specific asset lookups based on manifest structure
        match asset_name:
            case "src/tag-me.js" | "tag-me.js":
                # Look for JavaScript entry
                js_entry = manifest.get("src/tag-me.js", {})
                if file_path := js_entry.get("file", ""):
                    asset_path = f"tag_me/dist/{file_path}"
                else:
                    asset_path = "tag_me/dist/js/tag-me.js"
                return asset_path

            case name if name == "tag-me.css" or name.endswith(".css"):
                # Look for CSS in the JS entry (Vite includes CSS in JS manifest)
                js_entry = manifest.get("src/tag-me.js", {})
                css_files = js_entry.get("css", [])

                if css_files:
                    # Return the first CSS file (usually only one)
                    asset_path = f"tag_me/dist/{css_files[0]}"
                else:
                    asset_path = "tag_me/dist/css/tag-me.css"
                return asset_path

            case _:
                # Final fallback: return original path
                logger.warning(f"Unknown asset type: {asset_name}, using fallback path")
                return f"tag_me/dist/{asset_name}"

    except FileNotFoundError:
        msg = f"Warning: Vite manifest file not found for {asset_name}"
        logger.exception(msg)
        return f"tag_me/dist/{asset_name}"

    except json.JSONDecodeError:
        msg = f"Warning: Invalid JSON in Vite manifest for {asset_name}"
        logger.exception(msg)
        return f"tag_me/dist/{asset_name}"

    except KeyError as e:
        msg = f"Warning: Missing key in Vite manifest for {asset_name}: {e}"
        logger.exception(msg)
        return f"tag_me/dist/{asset_name}"


def get_tag_me_js():
    """Get the tag-me JS file path from manifest."""
    try:
        manifest_path = finders.find("tag_me/dist/.vite/manifest.json")
        if not manifest_path:
            logger.warning("Manifest not found, using fallback JS")
            return "tag_me/dist/js/tag-me.js"

        manifest = json.loads(Path(manifest_path).read_text())
        js_entry = manifest.get("src/tag-me.js", {})

        if file_path := js_entry.get("file", ""):
            return f"tag_me/dist/{file_path}"

        return "tag_me/dist/js/tag-me.js"
    except Exception as e:
        logger.exception(f"Error loading JS from manifest: {e}")
        return "tag_me/dist/js/tag-me.js"


def get_tag_me_css():
    """Get the tag-me CSS file path from manifest."""
    try:
        manifest_path = finders.find("tag_me/dist/.vite/manifest.json")
        if not manifest_path:
            logger.warning("Manifest not found, using fallback CSS")
            return "tag_me/dist/css/tag-me.css"

        manifest = json.loads(Path(manifest_path).read_text())

        # CSS is a separate entry called "style.css"
        css_entry = manifest.get("style.css", {})

        if file_path := css_entry.get("file", ""):
            return f"tag_me/dist/{file_path}"

        # Fallback to unhashed filename
        return "tag_me/dist/css/tag-me.css"
    except Exception as e:
        logger.exception(f"Error loading CSS from manifest: {e}")
        return "tag_me/dist/css/tag-me.css"
