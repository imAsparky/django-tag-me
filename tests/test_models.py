"""tag-me model tests"""

import logging
import string

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from tests.models import TaggedFieldTestModel

logger = logging.getLogger(__name__)


class TestTag(TestCase):
    """Test the Tags ABC"""

    def test_tag_model_default_properties(self):
        model = TaggedFieldTestModel()

        assert model.model_class_verbose_name == "Tagged Field Test Model"
        assert model.model_class_name == "TaggedFieldTestModel"

    def test_tag_slugify(self):
        model = TaggedFieldTestModel()

        tag = "asdf"
        assert tag in model.slugify(tag)

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
            tags=st_name,
        )

        # Note: We need to do some work on the slugify process first...
        # assert TagBase.slugify(tag.tags) in tag.slug

        assert len(tag.slug) >= 8
