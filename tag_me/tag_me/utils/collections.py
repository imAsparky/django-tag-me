"""tags app collections."""

# from collections.abc import MutableSequence

import json
import logging
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from tag_me.utils.parser import parse_tags


class FieldTagListFormatter(list):
    """A custom tags list.

    The modified methods prevent addition of duplicates in the tag list.

    Two additional methods `add_tags` and `del_tags` make use of
    django-tag-me `parse_tags` to enable multiple additions or deletions
    possible using a string of tags,  or a list of tags.

    See https://django-tag-fields.readthedocs.io/en/latest/forms.html for
    examples of how strings of tags are treated using `parse_tags`.
    """

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        tags: (
            dict[str : list[str] | set[str] | str]  # noqa: E203
            | list[str]
            | set[str]
            | str
            | None
        ) = None,
    ) -> None:

        super().__init__()
        self.tags = []
        self.add_tags(tags)

    def __add__(self, other):
        if isinstance(other, FieldTagListFormatter):
            return self.__class__(sorted(self.tags + other.tags))
        elif isinstance(other, type(self.tags)):
            return self.__class__(sorted(self.tags + other))
        return self.__class__(sorted(self.tags + list(other)))

    def __cast(self, other):
        return (
            other.tags if isinstance(other, FieldTagListFormatter) else other
        )

    def __contains__(self, item):
        return item in self.tags

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["tags"] = self.__dict__["tags"][:]
        return inst

    def copy(self):
        return self.__copy__()

    def __delitem__(self, i):
        del self.tags[i]

    def __eq__(self, other):
        return self.tags == self.__cast(other)

    def __ge__(self, other):
        return self.tags >= self.__cast(other)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.tags[i])
        else:
            return self.tags[i]

    def __gt__(self, other):
        return self.tags > self.__cast(other)

    def __iadd__(self, other):
        """Add all tags, duplicates are not removed."""
        if isinstance(other, FieldTagListFormatter):
            self.tags += other.tags
        elif isinstance(other, type(self.tags)):
            self.tags += other
        else:
            self.tags += list(other)
        self.tags = sorted(self.tags)
        return self

    def __imul__(self, n):
        self.tags *= n
        return self

    def __le__(self, other):
        return self.tags <= self.__cast(other)

    def __len__(self):
        return len(self.tags)

    def __lt__(self, other):
        return self.tags < self.__cast(other)

    def __mul__(self, n):
        return self.tags * n
        # return self.__class__(self.tags * n) Python return does not work here. # noqa: E501

    __rmul__ = __mul__

    def __radd__(self, other):
        if isinstance(other, FieldTagListFormatter):
            return self.__class__(sorted(other.tags + self.tags))
        elif isinstance(other, type(self.tags)):
            return self.__class__(sorted(other + self.tags))
        return self.__class__(sorted(list(other) + self.tags))

    def __repr__(self):
        return repr(self.tags)

    def __setitem__(self, i, item):
        if item not in self.tags:
            self.tags[i] = item

    @staticmethod
    def _is_valid_tag(tag: str) -> bool:
        """Checks if a tag is a valid string and not a null value."""
        null_pattern = re.compile(r"\bnull\b[\.,]?", re.IGNORECASE)
        return isinstance(tag, str) and not null_pattern.match(tag)

    @staticmethod
    def _is_valid_tag_container(tags: dict | list | set | str | None) -> bool:
        """
        Checks if the tag container is a valid type and, if a dict, contains
        the 'tags' key.

        Raises:
            ValidationError: If the tag container is a dict and doesn't have
                            the 'tags' key.
        """
        match tags:
            case dict():
                if "tags" not in tags:  # Check for the 'tags' key
                    raise ValidationError(
                        _(
                            "%(value)s The field dict must contain the key "
                            "'tags' with a value type str or set[str] or "
                            "list[str]. Keys supplied %(keys)s."
                        ),
                        params={
                            "value": tags,
                            "keys": tags.keys(),
                        },
                        code="invalid",
                    )
                return True  # Valid dictionary
            case list() | set() | str() | None:
                return True
            case _:  # Catch-all for invalid types
                return False

    def _is_valid_tag_list(self, tag_list: list[str]) -> bool:
        """Checks if all tags in a list are valid."""
        return all(self._is_valid_tag(tag) for tag in tag_list)

    def _extract_tags_from_dict(self, tags: dict[list[str] | str]) -> list:
        """Extracts and validates tags from a dictionary.

        :param tags: The input dictionary.

        :returns: A list of valid tags.

        :raises ValidationError: If the 'tags' key is missing, the value
                                 associated with 'tags' is invalid, or if an
                                 error occurs during tag validation.
        """
        try:
            if self._is_valid_tag_container(tags):
                inner_tags: str | list = tags["tags"]
                match inner_tags:
                    case str():
                        return parse_tags(inner_tags)
                    case list() | set():
                        if self._is_valid_tag_list(inner_tags):
                            return inner_tags
                        else:
                            raise ValidationError(
                                _(
                                    "%(value)s The dict must contain a value "
                                    "type str or set[str] or list[str]. Keys "
                                    "supplied %(keys)s. Value type %(values)s."
                                ),
                                params={
                                    "value": tags,
                                    "keys": tags.keys(),
                                    "values": type(tags.get("tags")),
                                },
                                code="invalid",
                            )
                    case _:  # Handles unexpected types
                        raise ValidationError(
                            _(
                                "%(value)s The dict must contain a value type "
                                "str or set[str] or list[str]. Keys supplied "
                                "%(keys)s. Value type %(values)s."
                            ),
                            params={
                                "value": tags,
                                "keys": tags.keys(),
                                "values": type(tags.get("tags")),
                            },
                            code="invalid",
                        )
        except ValidationError as e:
            self.logger.error("An invalid dictionary was passed %s", e)
            return []

    def _get_tag_list(
        self,
        tags: (
            dict[str : list[str] | set[str] | str]  # noqa: E203
            | list[str]
            | set[str]
            | str
            | None
        ) = None,
    ) -> list[str]:
        """
        Extracts a list of valid tags from various input types.

        Handles the following input types:

        * **dict:** Expects a dictionary where the value associated with the 'tags' key # noqa: E501
           is a list, set, or string of tags.
        * **list or set:**  Expects a list or set directly containing string tags. # noqa: E501
        * **str:** Expects a string containing tags (presumably delimited in some way). # noqa: E501
        * **None:** Returns an empty list.

        :param tags: The input to extract tags from. Can be a dictionary, list, set, string, or None. # noqa: E501
        :returns: A list of valid tags extracted from the input.
        :raises ValidationError: If the input `tags` is of an invalid type or the tags within are invalid. # noqa: E501
        """
        if tags is None:
            return []

        match tags:
            case dict():
                return self._extract_tags_from_dict(tags)
            case list() | set():
                if self._is_valid_tag_list(tags):
                    return tags
                else:
                    raise ValidationError(
                        _(
                            "%(value)s must be dict or list or set containing "
                            "strings, or a string or None, type is "
                            "%(val_type)s"
                        ),
                        params={"value": tags, "val_type": type(tags)},
                        code="invalid",
                    )
            case str():
                return parse_tags(tags)
            case _:
                raise ValidationError(
                    _(
                        "%(value)s must be dict or list or set containing "
                        "strings, or a string or None, type is %(val_type)s"
                    ),
                    params={"value": tags, "val_type": type(tags)},
                    code="invalid",
                )

    def _add_tags(
        self,
        tags: (
            dict[str : list[str] | set[str] | str]  # noqa: E203
            | list[str]
            | set[str]
            | str
            | None
        ) = None,
    ) -> list[str]:
        """Adds valid, unique tags to the internal tag list and returns the sorted list. # noqa: E501

        Handles the following input types:

        * **dict:** Expects a dictionary where the value associated with the 'tags' key # noqa: E501
           is a list, set, or string of tags.
        * **list or set:**  Expects a list or set directly containing string tags. # noqa: E501
        * **str:** Expects a string containing tags (presumably delimited in some way). # noqa: E501
        * **None:** Returns an empty list.


        :param tags: The input to extract tags from. Can be a dictionary, list, set, string, or None. # noqa: E501
        :returns: A sorted list of unique, valid tags added to the object's internal state. # noqa: E501
        :raises ValidationError: If the input `tags` is of an invalid type or the tags within are invalid. # noqa: E501
        """
        try:
            if self._is_valid_tag_container(tags):
                tag_list = self._get_tag_list(tags)

                for tag in tag_list:
                    if self._is_valid_tag(tag) and tag not in self.tags:
                        self.tags.append(tag)

                return sorted(self.tags)

            else:
                raise ValidationError(
                    _(
                        "%(value)s must be dict or list or set containing "
                        "strings, or a string or None, type is %(val_type)s"
                    ),
                    params={
                        "value": tags,
                        "val_type": type(tags),
                    },
                    code="invalid",
                )

        except ValidationError as e:

            self.logger.error(
                "An invalid tag or container was passed %s",
                e,
            )

            return []

    def add_tags(
        self,
        tags: (
            dict[str : list[str] | set[str] | str]
            | list[str]
            | set[str]
            | str
            | None
        ) = None,
    ) -> list[str]:
        """Allows addition of multiple tags to the tags list."""
        return self._add_tags(tags)

    def append(self, item):
        """S.append(value) -- append value to the end of the sequence"""
        return self.add_tags(item)

    def clear(self):
        """S.clear() -> None -- remove all items from S"""
        self.tags.clear()

    def count(self, item):
        return self.tags.count(item)

    def del_tags(
        self,
        tags: (
            dict[str : list[str] | set[str] | str]  # noqa: E203
            | list[str]
            | set[str]
            | str
            | None
        ) = None,
    ) -> list[str]:
        """Allows deletion of multiple tags from tags list."""
        tag_list = self._get_tag_list(tags)

        for tag in tag_list:
            if tag in self.tags:
                self.tags.remove(tag)
        # self.tags = sorted(self.tags)
        return sorted(self.tags)

    def extend(
        self,
        tags: (
            dict[str : list[str] | set[str] | str]  # noqa: E203
            | list[str]
            | set[str]
            | str
            | None
        ) = None,
    ) -> list[str]:
        """S.extend(dict, list, set or string) -- extend tags list by appending elements"""  # noqa: E501
        return self.add_tags(tags)

    def index(self, item, *args):
        return self.tags.index(item, *args)

    def insert(self, i, item):
        """S.insert(index, value) -- insert value before index"""

        if item not in self.tags:
            self.tags.insert(i, item)

    def pop(self, i=-1):
        """S.pop([index]) -> item -- remove and return item at index
        (default last).

        Raise IndexError if list is empty or index is out of range.
        """
        return self.tags.pop(i)

    def remove(self, item):
        """S.remove(value) -- remove the value."""
        if item in self.tags:
            self.tags.remove(item)

    def reverse(self):
        """S.reverse() -- reverse *IN PLACE*"""
        self.tags.reverse()

    def sort(self, /, *args, **kwargs):
        """S.sort() -- sort *IN PLACE*"""
        self.tags.sort(*args, **kwargs)

    def toCSV(self, include_trailing_comma: bool = False) -> str:
        """Typically used in the fields `from_db_value` to format the forms display."""  # noqa: E501
        csv = ""
        for tag in self.tags:
            csv = csv + f"{tag}, "

        match include_trailing_comma:
            case False:
                csv = csv[:-2]
            case True:
                csv = csv[:-1]

        return csv

    def toDict(self) -> dict[str : list[str]]:  # noqa: E203
        """Returns the tags as a dict {'tags': [tags]}."""
        return self.__dict__

    def toJson(self) -> str:
        """Returns the JSON string format of a dict {'tags': [tags]}."""
        return json.dumps(self.__dict__)

    def toList(self):
        """Returns the tags in a list format."""
        return list(self.tags)
