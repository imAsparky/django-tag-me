# tag_me/assets.py

import json
import logging
from pathlib import Path

from django.contrib.staticfiles import finders
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_vite_manifest():
    """
    Load and cache the Vite manifest.

    The manifest is cached for the lifetime of the Python process. The cache
    automatically clears on server restart, which is required when deploying
    new tag-me versions with updated assets anyway.

    Returns:
        dict: The parsed manifest JSON

    Raises:
        FileNotFoundError: If manifest not found
        ValueError: If manifest contains invalid JSON
    """
    manifest_path_str = finders.find("tag_me/dist/manifest.json")

    if not manifest_path_str:
        raise FileNotFoundError(
            "Vite manifest not found at tag_me/dist/manifest.json. "
            "Run 'npm run prod' to build assets."
        )

    manifest_path = Path(str(manifest_path_str))

    try:
        return json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in Vite manifest: {e}")


def get_tag_me_js():
    """
    Get the cache-busted JS file path.

    Returns:
        str: Path to hashed JS file (e.g., 'tag_me/dist/js/tag-me.abc123.js')

    Raises:
        FileNotFoundError: If manifest not found
        ValueError: If JS entry not in manifest
    """
    manifest = _load_vite_manifest()

    js_entry = manifest.get("src/tag-me.js", {})
    file_path = js_entry.get("file")

    if not file_path:
        raise ValueError(
            "JS entry 'src/tag-me.js' not found in manifest. "
            f"Available keys: {list(manifest.keys())}"
        )

    return f"tag_me/dist/{file_path}"


def get_tag_me_css():
    """
    Get the cache-busted CSS file path.

    Returns:
        str: Path to hashed CSS file (e.g., 'tag_me/dist/css/tag-me.def456.css')

    Raises:
        FileNotFoundError: If manifest not found
        ValueError: If CSS entry not in manifest
    """
    manifest = _load_vite_manifest()

    css_entry = manifest.get("style.css", {})
    file_path = css_entry.get("file")

    if not file_path:
        raise ValueError(
            "CSS entry 'style.css' not found in manifest. "
            f"Available keys: {list(manifest.keys())}"
        )

    return f"tag_me/dist/{file_path}"
