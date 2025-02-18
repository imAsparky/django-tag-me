import os
import sys


def stdout_with_optional_color(message, color_code=None):
    """
    30	Black
    31	Red
    32	Green
    33	Yellow
    34	Blue
    35	Magenta
    36	Cyan
    37	White
    90	Bright Black (Gray)
    91	Bright Red
    92	Bright Green
    93	Bright Yellow
    94	Bright Blue
    95	Bright Magenta
    96	Bright Cyan
    97	Bright White
    """
    if (
        color_code is not None and sys.stdout.isatty() and os.name != "nt"
    ):  # Check if TTY and not Windows
        message = f"\033[{color_code}m{message}\033[0m"
    sys.stdout.write(message + "\n")


"""
from tag_me.utils import helpers
mvb=UserTag.objects.get(id=1).model_verbose_name
fld=UserTag.objects.get(id=1).field_name
user=UserTag.objects.get(id=1).user
tags=helpers.get_user_field_choices_as_list_tuples(model_verbose_name=mvb, field_name=fld, user=user)
"""
