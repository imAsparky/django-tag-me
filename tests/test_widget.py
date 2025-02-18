from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from tag_me.models import (
    TaggedFieldModel,
    UserTag,
)
from tag_me.widgets import TagMeSelectMultipleWidget

User = get_user_model()


class TestTagMeSelectMultipleWidget(TestCase):
    """
    Test suite for the TagMeSelectMultipleWidget class.

    This class tests the rendering functionality of the TagMeSelectMultipleWidget,
    ensuring proper behavior with different input scenarios including user tags,
    predefined choices, empty values, and single values.
    """

    def setUp(self):
        """
        Set up test data before each test method.

        Creates:
            - A test user
            - Gets the first content type (required for TaggedFieldModel)
            - Gets a TaggedFieldModel instance with id=1
            - Creates a UserTag instance with sample tags
        """
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.content = ContentType.objects.first()
        from tests.models import TaggedFieldTestModel

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

        self.tagged_field = TaggedFieldModel.objects.get(id=1)
        # Create a UserTag instance
        self.user_tag = UserTag.objects.create(
            user=self.user, tagged_field=self.tagged_field, tags="tag1, tag2, tag3"
        )

    def test_render_with_user_tags(self):
        """
        Test widget rendering with user-specific tags.

        Verifies that:
            - All user tags are present in the rendered output
            - The field name is correctly rendered
            - The add-tag URL is correctly included
            - Specific tags (tag1, tag2, tag3) are present in output
        """
        widget = TagMeSelectMultipleWidget()
        widget.attrs = {
            "user": self.user,
            "tagged_field": self.tagged_field,
            "template": "tag_me/tag_me_select.html",
            "multiple": True,
            "auto_select_new_tags": True,
            "display_number_selected": 3,
            "field_verbose_name": "Test Field",
        }
        name = "test_tags"
        value = "tag1,tag2"

        result = widget.render(name, value)

        assert "tag1" in result
        assert "tag2" in result
        assert "tag3" in result
        assert name in result
        assert reverse("tag_me:add-tag", args=[self.user_tag.id]) in result

    def test_render_with_predefined_choices(self):
        """
        Test widget rendering with predefined choices instead of user tags.

        Verifies that:
            - Predefined choices are correctly rendered
            - The first choice is always an empty string
            - Tag addition is disabled (permittedToAddTags: false)
            - All choices (choice1, choice2, choice3) are present
        """
        predefined_choices = "choice1,choice2,choice3,"
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "template": "tag_me/tag_me_select.html",
                "tag_choices": predefined_choices,
                "multiple": True,
                "auto_select_new_tags": True,
                "display_number_selected": 3,
                "field_verbose_name": "Test Field",
            }
        )

        result = widget.render(
            name="test_tags",
            value="choice1",
        )

        assert "choice1" in result
        assert "choice2" in result
        assert "choice3" in result
        assert "permittedToAddTags: false" in result
        # Check first choice is always an empty string
        assert widget.choices[0] == ""

    def test_render_with_empty_value(self):
        """
        Test widget rendering when an empty value is provided.

        Verifies that:
            - Empty string is present in choices
            - Selected value is correctly rendered as an empty string
            - HTML encoding of selected empty value is correct
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field.id,
                "template": "tag_me/tag_me_select.html",
                "multiple": True,
                "auto_select_new_tags": True,
                "display_number_selected": 3,
                "field_verbose_name": "Test Field",
            }
        )
        name = "test_tags"
        value = ""

        result = widget.render(name, value)

        assert '""' in result  # Empty string should be in choices
        # check the selected value == ''
        assert "selected: [&#x27;&#x27;]" in result

    def test_render_with_single_value(self):
        """
        Test widget rendering with a single selected value.

        Verifies that:
            - Single value is correctly rendered in the selected attribute
            - HTML encoding of the selected value is correct
        """
        widget = TagMeSelectMultipleWidget(
            attrs={
                "user": self.user,
                "tagged_field": self.tagged_field.id,
                "template": "tag_me/tag_me_select.html",
                "multiple": True,
                "auto_select_new_tags": True,
                "display_number_selected": 3,
                "field_verbose_name": "Test Field",
            }
        )
        name = "test_tags"
        value = "tag1"

        result = widget.render(name, value)

        assert "selected: [&#x27;tag1&#x27;]" in result

    def tearDown(self):
        # Clean up created objects
        self.user.delete()


#         self.user_tag.delete()
