# templatetags/custom_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="tag_me_pills")
def tag_me_pills(value):
    """
     Templatetag that takes a comma-separated string and returns the list with
     html pills. Each pill is in a div with class flex to display like in forms.

    Usage: {{ my_string|tag_me_pills }}
    """

    if not value:
        return ""

    # Split the string by commas and strip whitespace
    items = [item.strip() for item in value.split(",")]

    # Wrap each item in indigo background div
    wrapped_items = [
        f'<div class="justify-center items-center font-medium px-2 rounded-full text-indigo-700 bg-indigo-100 border border-indigo-300 h-fit w-fit mr-1">{item}</div>'
        for item in items
        if item
    ]

    # Mark as safe HTML and return
    return mark_safe(f"{' '.join(wrapped_items)}\n")
