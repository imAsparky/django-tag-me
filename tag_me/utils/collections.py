"""tags app collections."""

# from collections.abc import MutableSequence

import json

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

    def __init__(self, tags: list[str] | str = None):
        self.tags = []
        self.add_tags(tags)
        print(f"#32 FieldTagList INIT {type(tags)} {tags}")

    def __add__(self, other):
        if isinstance(other, FieldTagListFormatter):
            return self.__class__(self.tags + other.tags)
        elif isinstance(other, type(self.tags)):
            return self.__class__(self.tags + other)
        return self.__class__(self.tags + list(other))

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
        inst.__dict__["data"] = self.__dict__["data"][:]
        return inst

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
        if isinstance(other, FieldTagListFormatter):
            self.tags += other.tags
        elif isinstance(other, type(self.tags)):
            self.tags += other
        else:
            self.tags += list(other)
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
        return self.__class__(self.tags * n)

    __rmul__ = __mul__

    def __radd__(self, other):
        if isinstance(other, FieldTagListFormatter):
            return self.__class__(other.tags + self.tags)
        elif isinstance(other, type(self.tags)):
            return self.__class__(other + self.tags)
        return self.__class__(list(other) + self.tags)

    def __repr__(self):
        return repr(self.tags)

    def __setitem__(self, i, item):
        if item not in self.tags:
            self.tags[i] = item

    def _get_tag_list(
        self,
        tags: dict[str : list[str] | set[str] | str]  # noqa: E203
        | list[str]
        | set[str]
        | str
        | None = None,
    ) -> list[str]:
        """Takes multiple input types and returns a list of tags."""
        match tags:
            case dict():
                # If there is a "tags" key, passing the "tags" values to
                # FieldTagList ensures that it passes validation.
                if "tags" in tags.keys():
                    match tags["tags"]:
                        case list() | set():
                            return list(set(tags["tags"]))
                        case str():
                            return parse_tags(tags["tags"])

                        case _:
                            raise ValidationError(
                                _(
                                    "%(value)s The field dict must contain a value type str or set[str] or list[str]. Keys supplied %(keys)s. Value type %(values)s."  # noqa: E501
                                ),
                                params={
                                    "value": tags,
                                    "keys": tags.keys(),
                                    "values": type(tags.get("tags")),
                                },
                                code="invalid",
                            )

                else:
                    raise ValidationError(
                        _(
                            "%(value)s The field dict must contain the key 'tags' with a value type str or set[str] or list[str]. Keys supplied %(keys)s."  # noqa: E501
                        ),
                        params={
                            "value": tags,
                            "keys": tags.keys(),
                        },
                        code="invalid",
                    )
            case list():
                return tags
            case None:
                return []
            case set():
                return list(tags)
            case str():
                return parse_tags(tags)
            case _:
                raise ValidationError(
                    _(
                        "%(value)s must be dict or list or set containing strings, or a string or None, type is %(val_type)s"  # noqa: E501
                    ),
                    params={
                        "value": tags,
                        "val_type": type(tags),
                    },
                    code="invalid",
                )

    def _add_tags(
        self,
        tags: dict[str : list[str] | set[str] | str]  # noqa: E203
        | list[str]
        | set[str]
        | str
        | None = None,
    ) -> list[str]:
        """Return a list of unique tags, without any null values."""
        tag_list = self._get_tag_list(tags)
        null_tags: list = [
            "null",
            "Null",
            "NULL",
        ]

        match tag_list:
            case list():
                for tag in tag_list:
                    match tag:
                        case str():
                            if tag not in self.tags and tag not in null_tags:
                                self.tags.append(tag)
                        case _:
                            raise ValidationError(
                                _(
                                    "%(value)s must be type <class 'str'>, type is %(val_type)s"  # noqa: E501
                                ),
                                params={
                                    "value": tag,
                                    "val_type": type(tag),
                                },
                                code="invalid",
                            )
                self.tags = sorted(self.tags)
                return self.tags
            case None:
                return self.tags

    def add_tags(
        self,
        tags: dict[str : list[str] | set[str] | str]  # noqa: E203
        | list[str]
        | set[str]
        | str
        | None = None,
    ) -> list[str]:
        """Allows addition of multiple tags to the tags list."""
        self._add_tags(tags)

    def append(self, item):
        """S.append(value) -- append value to the end of the sequence"""
        return self.add_tags(item)

    def clear(self):
        """S.clear() -> None -- remove all items from S"""
        self.tags.clear()

    def copy(self):
        return self.__class__(self)

    def count(self, item):
        return self.tags.count(item)

    def del_tags(
        self,
        tags: dict[str : list[str] | set[str] | str]  # noqa: E203
        | list[str]
        | set[str]
        | str
        | None = None,
    ) -> list[str]:
        """Allows deletion of multiple tags from tags list."""
        tag_list = self._get_tag_list(tags)

        match tag_list:
            case list():
                for tag in tag_list:
                    if tag in self.tags:
                        self.tags.remove(tag)
                self.tags = sorted(self.tags)
                return self.tags
            case None:
                return self.tags

    def extend(
        self,
        tags: dict[str : list[str] | set[str] | str]  # noqa: E203
        | list[str]
        | set[str]
        | str
        | None = None,
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
