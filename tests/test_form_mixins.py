"""tag-me form mixin tests"""

import logging

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.forms import CharField, ModelForm
from django.test import TestCase

from tag_me.db.forms.fields import TagMeCharField
from tag_me.db.forms.mixins import (
    AllFieldsTagMeModelFormMixin,
    TagMeModelFormMixin,
)
from tag_me.models import (
    TaggedFieldModel,
    UserTag,
)
from tag_me.widgets import TagMeSelectMultipleWidget
from tests.models import TaggedFieldTestModel

logger = logging.getLogger(__name__)

User = get_user_model()


class TestTagMeModelFormMixin(TestCase):
    """Test the TagMeModelFormMixin"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.tagged_model = TaggedFieldTestModel.objects.create(
            tagged_field_1="tag1,tag2", tagged_field_2="tag3,tag4"
        )

        # Create test forms dynamically in setUp to avoid database access during module import
        class TaggedFieldTestForm(TagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1", "tagged_field_2"]

        self.TaggedFieldTestForm = TaggedFieldTestForm

    def test_initialization_with_user(self):
        """Test form initialization with user parameter"""
        form = self.TaggedFieldTestForm(user=self.user)
        self.assertEqual(form.user, self.user)

    def test_initialization_without_user(self):
        """Test form initialization without user parameter"""
        form = self.TaggedFieldTestForm()
        self.assertIsNone(form.user)

    def test_tagme_field_widget_attributes(self):
        """Test that TagMeCharField widgets get proper attributes"""
        form = self.TaggedFieldTestForm(user=self.user)

        # Test both TagMeCharFields
        for field_name in ["tagged_field_1", "tagged_field_2"]:
            field = form.fields[field_name]
            self.assertIsInstance(field, TagMeCharField)
            self.assertEqual(field.widget.attrs["css_class"], "")
            self.assertEqual(field.widget.attrs["user"], self.user)

    def test_model_obj_handling(self):
        """Test form initialization with model_obj parameter"""
        form = self.TaggedFieldTestForm(model_obj=self.tagged_model)
        self.assertEqual(form.model_obj, self.tagged_model)

    def test_form_with_instance(self):
        """Test form initialization with an instance"""
        form = self.TaggedFieldTestForm(instance=self.tagged_model, user=self.user)
        self.assertEqual(form.initial["tagged_field_1"], "tag1,tag2")
        self.assertEqual(form.initial["tagged_field_2"], "tag3,tag4")


class TestAllFieldsTagMeModelFormMixin(TestCase):
    """Test the AllFieldsTagMeModelFormMixin"""

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpass")

        # Get content type for our test model
        self.content_type = ContentType.objects.get_for_model(TaggedFieldTestModel)

        # Create TaggedFieldModel entry
        self.tagged_field_model = TaggedFieldModel.objects.create(
            content=self.content_type,
            model_name=TaggedFieldTestModel._meta.object_name,
            field_name="tagged_field_1",
            tag_type="user",
            field_verbose_name="Tagged Field 1",
        )

        # Create UserTag
        self.user_tag = UserTag.objects.create(
            user=self.user,
            model_name=TaggedFieldTestModel._meta.object_name,
            field_name="tagged_field_1",
            field_verbose_name="Tagged Field 1",
            tags="tag1,tag2,tag3",
        )

        # Create test form
        class AllFieldsTaggedTestForm(AllFieldsTagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1"]

        self.AllFieldsTaggedTestForm = AllFieldsTaggedTestForm

    def test_widget_creation(self):
        """Test that the correct widget is created with proper configuration"""
        form = self.AllFieldsTaggedTestForm(user=self.user)

        # Check field configuration
        field = form.fields["tagged_field_1"]
        assert isinstance(field, CharField)
        assert isinstance(field.widget, TagMeSelectMultipleWidget)

        # Verify widget attributes
        widget_attrs = field.widget.attrs
        assert widget_attrs["all_tag_fields_mixin"] is True
        assert (
            widget_attrs["display_all_tags"] is False
        )  # Ensures tag creation/editing is disabled
        assert widget_attrs["user"] == self.user
        assert widget_attrs["all_tag_fields_tag_string"] == "tag1,tag2,tag3"

    def test_missing_user_tag(self):
        """Test behavior when UserTag doesn't exist for a field"""
        # Delete the UserTag
        self.user_tag.delete()

        form = self.AllFieldsTaggedTestForm(user=self.user)

        # Field should remain as original TagMeCharField
        field = form.fields["tagged_field_1"]
        assert isinstance(field, TagMeCharField)

    def test_no_user_provided(self):
        """Test that form requires a user"""
        with pytest.raises(ObjectDoesNotExist):
            self.AllFieldsTaggedTestForm()
