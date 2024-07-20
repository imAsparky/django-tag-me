"""Test tags tagged field utils."""

# import subprocess
# from io import StringIO
# from contextlib import redirect_stdout

from io import StringIO

# import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command

# from django.contrib.contenttypes.models import ContentType
# from django.core import management
# from django.core.exceptions import ValidationError
# from django.test import override_settings
# from hypothesis import given
# from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from tag_me.models import TaggedFieldModel, UserTag
from tag_me.utils.helpers import (  # update_models_with_tagged_fields_table,
    get_model_content_type,
    get_model_tagged_fields_choices,
    get_model_tagged_fields_field_and_verbose,
    get_models_with_tagged_fields,
    get_models_with_tagged_fields_choices,
    get_user_field_choices_as_list_tuples,
    update_models_with_tagged_fields_table,
)

User = get_user_model()


class TestTagHelpers(TestCase):
    """Test the tags helper
    Uses `tests` models to make these tests.  This way we can have an
    explicit test set up.
    """

    def setUp(self):
        # make sure all migrations are up to date
        self.out_makemigration = StringIO()

        call_command(
            "makemigrations",
            stdout=self.out_makemigration,
        )

        # Run migrations so the tags management commads are run
        self.out_migration = StringIO()
        call_command(
            "migrate",
            stdout=self.out_migration,
        )

        _model = "TaggedFieldTestModel"
        _field_1 = "tagged_field_1"
        _field_2 = "tagged_field_2"

        self.tag_string1 = '"apple ball cat'
        self.tag_string1_result = [
            "apple",
            "ball",
            "cat",
        ]
        self.tag_string2 = "tree, flower cactus"

        self.tag_string3 = "car, truck plane"

        self.user1 = User.objects.create(
            username="user1",
            password="pw_user1",
            email="user1@email.com",
        )
        self.user2 = User.objects.create(
            username="user2",
            password="pw_user2",
            email="user2@email.com",
        )
        self.user3 = User.objects.create(
            username="user3",
            password="pw_user3",
            email="user3@email.com",
        )
        # Add all the users to the UserTag table.
        call_command(
            "add_user_tags",
            stdout=self.out_migration,
        )

        self.model_1_field_1 = TaggedFieldModel.objects.get(
            model_name=_model,
            field_name=_field_1,
        )
        self.model_1_field_2 = TaggedFieldModel.objects.get(
            model_name=_model,
            field_name=_field_2,
        )

        self.user1_tag1 = UserTag.objects.get(
            tagged_field=self.model_1_field_1,
            user=self.user1,
        )
        self.user1_tag1.tags = "User1 Tag1"
        self.user1_tag1.save()

        self.user2_tag1 = UserTag.objects.get(
            tagged_field=self.model_1_field_1,
            user=self.user2,
        )
        self.user2_tag1.tags = "User2 Tag1"
        self.user2_tag1.save()

        self.user3_tag1 = UserTag.objects.get(
            tagged_field=self.model_1_field_1,
            user=self.user3,
        )
        self.user3_tag1.tags = "User3 Tag1"
        self.user3_tag1.save()

    def test_get_model_tagged_fields_field_and_verbose_empty_verbose(self):
        fields = get_model_tagged_fields_field_and_verbose(
            model_verbose_name="",
        )
        assert fields == [(None, None)]

    def test_get_models_with_tagged_fields_apps_in_INSTALLED(self):
        with self.settings(PROJECT_APPS=None):
            models = get_models_with_tagged_fields()

            assert "<class 'tests.models.Post'>" in str(models)
            assert "<class 'tests.models.TaggedFieldTestModel'>" in str(models)

    def test_get_models_with_tagged_fields_apps_in_PROJECT(self):
        with self.settings(PROJECT_APPS=settings.INSTALLED_APPS):
            models = get_models_with_tagged_fields()

            assert "<class 'tests.models.Post'>" in str(models)
            assert "<class 'tests.models.TaggedFieldTestModel'>" in str(models)

    def test_get_models_with_tagged_fields(self):
        fields = get_models_with_tagged_fields()

        assert "<class 'tests.models.TaggedFieldTestModel'>" in str(fields)
        assert "<class 'tests.models.Post'>" in str(fields)

    def test_get_models_with_tagged_fields_choices(self):
        choices = get_models_with_tagged_fields_choices()

        assert "('Tagged Field Test Model', 'Tagged Field Test Model')" in str(
            choices
        )

    def test_get_model_tagged_fields_choices_with_feature_name(self):
        choices1 = get_model_tagged_fields_choices(
            feature_name="Tagged Field Test Model"
        )

        assert "('Tagged Field 1', 'Tagged Field 1')" in str(choices1)

        assert "('Tagged Field 2', 'Tagged Field 2')" in str(choices1)

    def test_get_model_tagged_fields_choices_without_feature_name(self):
        choices1 = get_model_tagged_fields_choices(feature_name="")

        assert choices1 == [(None, None)]

    def test_get_model_content_type_with_verbose(self):
        content = get_model_content_type(
            model_verbose_name="Tagged Field Test Model",
        )

        assert content.app_label == "tests"
        assert content.model == "taggedfieldtestmodel"

    def test_get_model_content_type_with_out_verbose(self):
        content = get_model_content_type(
            model_verbose_name="",
        )

        assert content is None

    def test_get_user_field_choices_as_list_tuples(self):
        choices_all = UserTag.objects.all()
        choices_1 = get_user_field_choices_as_list_tuples(
            model_verbose_name="Tagged Field Test Model",
            field_name="tagged_field_1",
            user=self.user1,
        )
        choices_2 = get_user_field_choices_as_list_tuples(
            model_verbose_name="Tagged Field Test Model",
            field_name="tagged_field_1",
            user=self.user2,
        )

        choices_3 = get_user_field_choices_as_list_tuples(
            model_verbose_name="Tagged Field Test Model",
            field_name="tagged_field_1",
            user=self.user3,
        )

        assert self.user1_tag1 in choices_all and choices_1
        assert self.user2_tag1 in choices_all and choices_2
        assert self.user3_tag1 in choices_all and choices_3
        #
        assert self.user1_tag1 not in choices_2 and choices_3
        assert self.user2_tag1 not in choices_1 and choices_3
        assert self.user3_tag1 not in choices_1 and choices_2

    def test_tagged_field_models_table_populated_ok(self):
        TaggedFieldModel.objects.all().delete()
        assert not TaggedFieldModel.objects.all().exists()
        update_models_with_tagged_fields_table()
        assert TaggedFieldModel.objects.all().exists()
