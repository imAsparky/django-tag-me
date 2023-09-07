"""Test tags tagged field utils."""
# import subprocess
# from io import StringIO
# from contextlib import redirect_stdout

# import pytest
# from django.conf import settings
from django.contrib.auth import get_user_model

# from django.contrib.contenttypes.models import ContentType
# from django.core import management
# from django.core.exceptions import ValidationError
# from django.test import override_settings
# from hypothesis import given
# from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from tag_me.utils.helpers import (  # update_models_with_tagged_fields_table,
    get_model_tagged_fields_choices,
    get_models_with_tagged_fields,
    get_models_with_tagged_fields_choices,
)

User = get_user_model()


class TestTagHelpers(TestCase):
    """Test the tags helper
    Uses `tests` models to make these tests.  This way we can have an
    explicit test set up.
    """

    def test_get_models_with_tagged_fields(self):
        fields = get_models_with_tagged_fields()

        assert "<class 'tests.models.TaggedFieldTestModel'>" in str(fields)

    def test_get_models_with_tagged_fields_choices(self):
        choices = get_models_with_tagged_fields_choices()

        assert "('Tagged Field Test Model', 'Tagged Field Test Model')" in str(
            choices
        )

    def test_get_model_tagged_fields_choices(self):
        choices1 = get_model_tagged_fields_choices(
            feature_name="Tagged Field Test Model"
        )

        assert "('Tagged Field 1', 'Tagged Field 1')" in str(choices1)

        assert "('Tagged Field 2', 'Tagged Field 2')" in str(choices1)

        # def test_core_update_models_with_tagged_fields_table(self):
        """This test is broken.
        The stdout capture is returning empty, followed Django docs and various
        other solutions.

        It works with the migrate command, so follow up with the tags command is needed.
        **************** See Issue-719 in TB *****************
        """
        # update = ""
        # update = StringIO()

        # with open(
        #     "tests/tests_backend/tests_tags/test_utils.txt", "w"
        # ) as update:
        #     # management.call_command("tags", "--update", stderr=update)
        #     management.call_command("migrate", stdout=update)

        # print(f"\nGETTING VALUE\t{update.getvalue()}\nDID IT WORK")
        # print(f"\nGETTING VALUE {update.getvalue()}")
        # call_command("tags", "-U", stdout=update)

        # assert (
        #     "Created BASE: BaseSoftLogS3ModelChild : tagged_field_1"
        #     in update.getvalue()
        # )

        # assert "Created BASE: BaseSoftLogS3ModelChild : tagged_field_2" in str(
        #     update.getvalue()
        # )

        # assert (
        #     "Created BASE: BaseSoftLogS3ModelChildNoLog : tagged_field_3"
        #     in str(update.getvalue())
        # )

        # assert (
        #     "Created BASE: BaseSoftLogS3ModelChildNoLog : tagged_field_4"
        #     in str(update.getvalue())
        # )
