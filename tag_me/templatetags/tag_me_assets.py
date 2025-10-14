# tag_me/templatetags/tag_me_assets.py

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

    Usage:
        {% load tag_me_assets %}
        <script src="{% tag_me_js %}"></script>
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

    Usage:
        {% load tag_me_assets %}
        {% tag_me_assets %}
    """
    css_url = static(get_tag_me_css())
    js_url = static(get_tag_me_js())

    return mark_safe(
        f'<link rel="stylesheet" href="{css_url}">\n<script src="{js_url}"></script>'
    )
