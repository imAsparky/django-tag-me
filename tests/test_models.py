"""tag-me model tests"""

import logging
import re
import string

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase, from_model

from tests.models import TaggedFieldTestModel

logger = logging.getLogger(__name__)


class TestTag(TestCase):
    """Test the Tags ABC"""

    @given(
        st_name=st.text(
            # alphabet=st.characters(
            #     blacklist_categories=[
            #         "Cs",
            #         "Cc",
            #     ],
            #     # codec="ascii",
            # ),
            alphabet=string.ascii_letters,
            min_size=1,
            max_size=50,
        )
    )
    def test_base_created_no_unicode_ok(
        self,
        st_name,
    ):
        tag = TaggedFieldTestModel.objects.create(
            name=st_name,
        )

        assert slugify(tag.name) in tag.slug
        assert len(tag.slug) >= 8
