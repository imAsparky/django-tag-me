"""Tag-Me parser functions"""

import unicodedata
from typing import Callable

from django.conf import settings
from django.utils.module_loading import import_string

# from tag_me.models import UserTag
bidi_control_chars = [
    "\u202a",  # LRE (Left-to-Right Embedding)
    "\u202b",  # RLE (Right-to-Left Embedding)
    "\u202c",  # PDF (Pop Directional Formatting)
    "\u202d",  # LRO (Left-to-Right Override)
    "\u202e",  # RLO (Right-to-Left Override)
]
device_control_chars = [chr(i) for i in range(0, 32)]
information_separator_chars = ["\x1f", "\x1e", "\x1d"]
other_control_chars = ["\x85", "\r"]
pua_chars_1 = [chr(i) for i in range(0xE000, 0xF8FF + 1)]  # Plane 0
pua_chars_2 = [chr(i) for i in range(0xF0000, 0xFFFFD + 1)]  # Plane 15
pua_chars_3 = [chr(i) for i in range(0x100000, 0x10FFFD + 1)]  # Plane 16
whitespace_chars = ["\n", "\x0b", "\x0c", "\t"]

exclude_chars: list = []
exclude_chars.extend(bidi_control_chars)
exclude_chars.extend(device_control_chars)
exclude_chars.extend(information_separator_chars)
exclude_chars.extend(other_control_chars)
exclude_chars.extend(pua_chars_1)
exclude_chars.extend(pua_chars_2)
exclude_chars.extend(pua_chars_3)
exclude_chars.extend(whitespace_chars)


def is_valid_char(char: str) -> bool:
    """
    Determines if a character is suitable for inclusion within a tag.

    Employs string methods and the `unicodedata` module for nuanced character
    filtering.

    :param char: A single character to be evaluated.
    :type char: str
    :returns: True if the character is valid for a tag, False otherwise.
    :rtype: bool

    **Filtering Criteria:**

    * **Alphanumeric Characters:** Letters and numbers are allowed (`str.isalnum()`). # noqa: E501
    * **Standard Whitespace:** Common whitespace (space, tab, etc.) is permitted (`str.isspace()`). # noqa: E501
    * **Quotation Marks:** Double (") and single (') quotes are explicitly allowed. # noqa: E501
    * **Commas:** The comma (,) is explicitly allowed for flexibility in tag delimiters. # noqa: E501
    * **Unicode Character Categories:**  The `unicodedata` module is used to exclude: # noqa: E501
        * Cc (Other, Control)
        * Cf (Other, Format)
        * Cs (Other, Surrogate)
        * Co (Other, Private Use)
        * Cn (Other, Not Assigned)

    .. important::
        This function filters out control characters, including the null
        character.

        See the Unicode documentation for details on character categories.
    """

    if char in exclude_chars:
        return False

    match char:
        case '"':
            return True
        case "'":
            return True
        case ",":
            return True

        # Handle alphanumeric and whitespace characters
    if char.isalnum() or char.isspace():
        return True

        # Fallback to category check (only if the above conditions weren't met)
    category = unicodedata.category(char)
    return category not in ["Cc", "Cf", "Cs", "Co", "Cn"]


def remove_control_chars(string: str) -> str:
    """
    Removes non-printable control characters from a string.

    Focuses on removing characters from the "Cc" Unicode category
    (e.g., tab, newline, etc.) and other potentially disruptive formatting
    codes. This includes characters from categories such as Cf (Format),
    Cs (Surrogate), Co (Private Use), and Cn (Not Assigned).

    :param string: The string to be cleaned.
    :type string: str

    :returns: A copy of the input string with control characters removed.
    :rtype: str

    **Example:**
        >>> input_string = "Hello\tWorld!\n"  # Contains tab and newline
        >>> cleaned_string = remove_control_chars(input_string)
        >>> print(cleaned_string)  # Output: "HelloWorld!"

    .. note::
        This function relies on the `is_valid_char` function for precise character filtering.
    """

    clean_string = "".join(c for c in string if is_valid_char(c))

    return clean_string


def _parse_tags(tag_string: str) -> list[str]:
    """
    Parses a string of tags, handling multiple words, commas, and quotation marks. # noqa:E501

    This function is intended for internal use. It extracts unique tags,
    respecting the following conventions:

    * **Commas as Delimiters:** Words separated by commas are treated as individual tags. # noqa:E501
    * **Quotation Mark Precedence:** Content within double quotes is treated as a single tag, even if it contains commas. # noqa:E501

    **Parsing Approach:** The function iterates through the tag string, tracking quotation marks and splitting the text into chunks for further processing. # noqa:E501

    :param tag_string: The raw string of tags to be parsed.
    :type tag_string: str

    :returns: A sorted list of unique tag names.
    :rtype: list

    **Ported from Jonathan Buchanan's django-tagging
    <http://django-tagging.googlecode.com/>_**
    """
    if not tag_string:
        return []

    # Remove control characters
    tag_string = remove_control_chars(tag_string)

    # Special case - if there are no commas or double quotes in the
    # input, we don't *do* a recall... I mean, we know we only need to
    # split on spaces.
    if "," not in tag_string and '"' not in tag_string:
        words = list(set(split_strip(tag_string, " ")))
        words.sort()
        return words

    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there are
    # any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(tag_string)
    try:
        while True:
            c = next(i)
            if c == '"':
                if buffer:
                    to_be_split.append("".join(buffer))
                    buffer = []
                # Find the matching quote
                open_quote = True
                c = next(i)
                while c != '"':
                    buffer.append(c)
                    c = next(i)
                if buffer:
                    word = "".join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == ",":
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer as unquoted.
        if buffer:
            if open_quote and "," in buffer:
                saw_loose_comma = True
            to_be_split.append("".join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = ","
        else:
            delimiter = " "
        for chunk in to_be_split:
            words.extend(split_strip(chunk, delimiter))

    words = list(set(words))
    words.sort()
    return words


def split_strip(string: str, delimiter: str = ",") -> list[str]:
    """
    Splits a string into a list, removes leading/trailing whitespace, and filters out empty entries. # noqa: E501

    This function combines splitting on a delimiter with whitespace removal,
    making it ideal for parsing string inputs where individual elements might
    contain extra spaces.

    :param string: The input string to be processed.
    :type string: str
    :param delimiter: The character or substring used to split the string (defaults to a comma). # noqa: E501
    :type delimiter: str

    :returns: A list of cleaned, non-empty elements.
    :rtype: list

    **Ported from Jonathan Buchanan's django-tagging
    <http://django-tagging.googlecode.com/>_**
    """
    if not string:
        return []

    words = [w.strip() for w in string.split(delimiter)]
    return [w for w in words if w]


def _edit_string_for_tags(tags: list = []) -> str:
    """
    Formats a list of tags into a user-editable string representation.
    Ensures the original tags can be accurately reconstructed from the
    formatted string.

    **Formatting Rules:**

    * **Tags with Commas or Spaces:** Enclosed in double quotes for preservation. # noqa: E501
    * **Delimiter Choice:**
        * Commas are used as delimiters if any unquoted tag contains whitespace. # noqa: E501
        * Otherwise, spaces are used as delimiters.

    :param tags:  A list of `UserTag` objects (optional).
    :type tags: list[UserTag]

    :returns: A formatted string representing the input tags.
    :rtype: str

    **Ported from Jonathan Buchanan's django-tagging
    <http://django-tagging.googlecode.com/>_**
    """
    names = []
    for tag in tags:
        name = tag.tags
        if "," in name or " " in name:
            names.append('"%s"' % name)
        else:
            names.append(name)
    return ", ".join(sorted(names))


def get_func(
    key: str = "",
    default: Callable = None,
) -> Callable:
    """Retrieves a function to be executed, either from settings or a default.

    This function helps you use functions that are configured in your Django
    project's settings file. Here's how it works:

    1. **Checks Your Settings:** It looks for a setting with the name you
    provide in the `key` parameter.  If found, the function 'path' stored in
    settings is used.

    2. **Provides a Fallback:** If no setting is found, or the setting doesn't
    point to a valid function, the `default` function (if you provided one) is
    used instead.

    :param key: The name of the setting where the function's 'path' is stored. (Optional) # noqa:E501
    :type key: str
    :param default: A function to use if no matching setting is found. (Optional) # noqa:E501
    :type default: Callable
    :returns: The function retrieved from settings or the provided default function. # noqa:E501
    :rtype: Callable
    """

    func_path = getattr(settings, key, None)
    return default if func_path is None else import_string(func_path)


def parse_tags(tag_string: list[str] | str = "") -> Callable | list[str]:
    """
    Delegates tag parsing to a dynamically selected function.

    This function prioritizes a custom tag parsing function specified in a
    settings configuration (`TAGME_GET_TAGS_FROM_STRING`). If no custom
    function is defined, it falls back to the default `_parse_tags`
    implementation.

    :param tag_string: The string containing tags.
    :type tag_string: str

    :returns: A callable function responsible for parsing tags.
    :rtype: Callable
    """
    func = get_func("TAGME_GET_TAGS_FROM_STRING", _parse_tags)
    return func(tag_string)


def edit_string_for_tags(tags: list = []) -> str:
    """
    Formats a list of tags into a string suitable for user editing.

    This function dynamically selects the appropriate method for converting
    tags into an editable string. It checks a settings configuration
    (`TAGME_GET_STRING_FROM_TAGS`) to determine the preferred method.

    :param tags: A list of tags (optional).
    :type tags: list

    :returns: A formatted string representation of the input tags.
    :rtype: str
    """

    func = get_func("TAGME_GET_STRING_FROM_TAGS", _edit_string_for_tags)
    return func(tags)
