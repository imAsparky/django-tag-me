from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from hypothesis.extra.django import TestCase

from tag_me.models import UserTag
from tag_me.utils.parser import edit_string_for_tags, parse_tags, split_strip

User = get_user_model()


class TestTagStringParser(SimpleTestCase):
    """These tests cover what isnt hit with test_collections.py"""

    def test_empty_string(self):
        tags = parse_tags("")

        assert tags == []

    def test_split_strip_empty(self):
        tags = split_strip("")

        assert tags == []


class TestTagsStringEdit(TestCase):
    def test_edit_string(self):
        user = User.objects.create(
            username="User1",
            password="pass",
            email="user1@email.com",
        )
        assert user.username == "User1"
        tag1 = UserTag.objects.create(name="tag1")
        tag2 = UserTag.objects.create(name="tag,2")
        tag3 = UserTag.objects.create(name="tag 3")

        tag_list = [
            tag1,
            tag2,
            tag3,
        ]

        assert edit_string_for_tags(tag_list) == '"tag 3", "tag,2", tag1'
