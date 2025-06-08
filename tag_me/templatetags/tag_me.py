# templatetags/custom_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="tag_me_pills")
def tag_me_pills(value):
    """
    Templatetag that takes a comma-separated string and returns the list with
    html pills. Each pill is styled consistently with the interactive tag component.
    Usage: {{ my_string|tag_me_pills }}
    """
    if not value:
        return ""

    # Split the string by commas and strip whitespace
    items = [item.strip() for item in value.split(",")]

    # Wrap each item with consistent pill styling (matches interactive component)
    wrapped_items = [
        f'<div class="inline-flex justify-center items-center font-medium py-1.5 px-3 rounded-full text-indigo-800 bg-indigo-50 border border-indigo-200 shadow-sm mr-2 mb-1">{item}</div>'
        for item in items
        if item
    ]

    # Mark as safe HTML and return
    return mark_safe(f"{' '.join(wrapped_items)}\n")


# @register.filter(name="tag_me_pills")
# def tag_me_pills(value):
#     """
#      Templatetag that takes a comma-separated string and returns the list with
#      html pills. Each pill is in a div with class flex to display like in forms.
#
#     Usage: {{ my_string|tag_me_pills }}
#     """
#
#     if not value:
#         return ""
#
#     # Split the string by commas and strip whitespace
#     items = [item.strip() for item in value.split(",")]
#
#     # Wrap each item in indigo background div
#     wrapped_items = [
#         f'<div class="justify-center items-center font-medium px-2 rounded-full text-indigo-700 bg-indigo-100 border border-indigo-300 h-fit w-fit mr-1">{item}</div>'
#         for item in items
#         if item
#     ]
#
#     # Mark as safe HTML and return
#     return mark_safe(f"{' '.join(wrapped_items)}\n")
