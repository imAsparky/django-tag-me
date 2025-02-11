"""tag-me form mixin tests"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelForm
from hypothesis.extra.django import TestCase

from tag_me.db.forms.fields import TagMeCharField
from tag_me.db.forms.mixins import (
    AllFieldsTagMeModelFormMixin,
    TagMeModelFormMixin,
)
from tag_me.models import TaggedFieldModel, UserTag
from tag_me.widgets import TagMeSelectMultipleWidget
from tests.models import Post, TaggedFieldTestModel

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

        # Create TaggedFieldModel entries for both fields
        self.tagged_field_models = [
            TaggedFieldModel.objects.create(
                content=self.content_type,
                model_name=TaggedFieldTestModel._meta.object_name,
                field_name="tagged_field_1",
                tag_type="user",
                field_verbose_name="Tagged Field 1",
            ),
            TaggedFieldModel.objects.create(
                content=self.content_type,
                model_name=TaggedFieldTestModel._meta.object_name,
                field_name="tagged_field_2",
                tag_type="system",
                field_verbose_name="Tagged Field 2",
            ),
        ]

        # Create corresponding UserTag for the user-type field
        self.user_tag = UserTag.objects.create(
            user=self.user,
            model_name=TaggedFieldTestModel._meta.object_name,
            field_name="tagged_field_1",
            field_verbose_name="Tagged Field 1",
            tags="initial_tag1,initial_tag2,initial_tag3",
        )

        # Create test form dynamically in setUp
        class AllFieldsTaggedTestForm(AllFieldsTagMeModelFormMixin, ModelForm):
            class Meta:
                model = TaggedFieldTestModel
                fields = ["tagged_field_1", "tagged_field_2"]

        self.AllFieldsTaggedTestForm = AllFieldsTaggedTestForm

    # NOTE: Commented out pending updates to mixins
    # def test_initialization_with_user(self):
    #     """Test form initialization with user parameter"""
    #     form = self.AllFieldsTaggedTestForm(user=self.user)
    #     self.assertEqual(form.user, self.user)

    # def test_user_tag_field_creation(self):
    #     """Test that user tag fields are properly created"""
    #     form = self.AllFieldsTaggedTestForm(user=self.user)
    #
    #     # Check if the user tag field was created properly
    #     self.assertIn("tagged_field_1", form.fields)
    #     field = form.fields["tagged_field_1"]
    #
    #     # Check field properties
    #     self.assertIsInstance(field.widget, TagMeSelectMultipleWidget)
    #     self.assertEqual(field.label, "Tagged Field 1")
    #     self.assertFalse(field.required)
    #
    #     # Check widget attributes
    #     widget_attrs = field.widget.attrs
    #     self.assertTrue(widget_attrs["all_tag_fields_mixin"])
    #     self.assertFalse(widget_attrs["display_all_tags"])
    #     self.assertEqual(widget_attrs["user"], self.user)
    #     self.assertEqual(
    #         widget_attrs["tag_string"], "initial_tag1,initial_tag2,initial_tag3"
    #     )

    # def test_system_tag_handling(self):
    #     """Test handling of system tags"""
    #     form = self.AllFieldsTaggedTestForm(user=self.user)
    #     # System tag field should still be present but not modified
    #     self.assertIn("tagged_field_2", form.fields)
    #     field = form.fields["tagged_field_2"]
    #     self.assertIsInstance(field, TagMeCharField)

    def test_initialization_without_user(self):
        """Test form initialization without user parameter"""
        with self.assertRaises(UserTag.DoesNotExist):
            self.AllFieldsTaggedTestForm()

    # def test_form_submission(self):
    #     """Test form submission with valid data"""
    #     form_data = {
    #         "tagged_field_1": "new_tag1,new_tag2",
    #         "tagged_field_2": "system_tag1,system_tag2",
    #     }
    #     form = self.AllFieldsTaggedTestForm(data=form_data, user=self.user)
    #     self.assertTrue(form.is_valid())
