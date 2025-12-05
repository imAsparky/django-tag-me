# tag_me/templatetags/tag_me_assets.py
"""
Template tags for loading Tag-Me assets.

These tags provide cache-busted URLs from the Vite manifest,
ensuring correct asset versions are loaded in production.
"""

from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from tag_me.assets import (
    get_tag_me_css,
    get_tag_me_js,
)

register = template.Library()


@register.simple_tag
def tag_me_js():
    """
    Returns the URL to the tag-me JavaScript file.

    When including manually, always use the `defer` attribute to ensure
    the script executes after Alpine.js (which loads as an ES module).

    Usage:
        {% load tag_me_assets %}
        <script defer src="{% tag_me_js %}"></script>
    """
    return static(get_tag_me_js())


@register.simple_tag
def tag_me_css():
    """
    Returns the URL to the tag-me CSS file.

    Usage:
        {% load tag_me_assets %}
        <link rel="stylesheet" href="{% tag_me_css %}">
    """
    return static(get_tag_me_css())


@register.simple_tag
def tag_me_assets():
    """
    Returns both JS and CSS as HTML tags ready to insert.

    The script uses 'defer' to ensure it executes after the document is parsed,
    giving Alpine.js (loaded via ES modules) time to initialize first.

    Note: tag-me.js is built as an IIFE bundle, not an ES module, so we use
    'defer' rather than 'type="module"'.

    Usage:
        {% load tag_me_assets %}

        {# In your base template, AFTER your main JS bundle that includes Alpine #}
        {% tag_me_assets %}

    Example with Vite:
        {% vite_asset 'main' %}   {# Loads Alpine.js #}
        {% tag_me_assets %}        {# Loads tag-me after Alpine #}

    Example with CDN:
        <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
        {% tag_me_assets %}
    """
    css_url = static(get_tag_me_css())
    js_url = static(get_tag_me_js())
    return mark_safe(
        f'<link rel="stylesheet" href="{css_url}">\n'
        f'<script defer src="{js_url}"></script>'
    )
