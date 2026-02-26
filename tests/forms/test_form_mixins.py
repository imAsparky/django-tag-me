"""
Tests for tag-me form mixins.

Covers:
    - TagMeModelFormMixin: __init__ kwarg extraction, cooperative user sharing,
      _configure_tagme_widgets behaviour, debug logging
    - AllFieldsTagMeModelFormMixin: user requirement, cooperative user sharing,
      dynamic field creation, FK-based lookup resilience, debug logging

Tests absorbed from test_fk_migration.py:
    - TestFormMixinFKIntegration (FK lookup, stale model_name)

Run with: pytest tests/test_form_mixins.py -v
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.forms import CharField, Form

from tag_me.forms.fields import TagMeCharField
from tag_me.forms.mixins import AllFieldsTagMeModelFormMixin, TagMeModelFormMixin
from tag_me.models import UserTag
from tests.models import TaggedFieldTestModel

User = get_user_model()


# ---------------------------------------------------------------------------
# Test form classes — defined inside a fixture because TagMeCharField.__init__
# touches the DB.  The fixture gives every test class access via `form_classes`.
# ---------------------------------------------------------------------------


@pytest.fixture
def form_classes(db):
    """Lazily define form classes that contain TagMeCharField.

    TagMeCharField hits the DB at class-definition time, so these
    cannot live at module level.
    """

    class SimpleTagMeForm(TagMeModelFormMixin, Form):
        """Form with one TagMeCharField for testing widget configuration."""

        my_tags = TagMeCharField(required=False)

    class MixedFieldForm(TagMeModelFormMixin, Form):
        """Form with both TagMeCharField and regular CharField."""

        tags = TagMeCharField(required=False)
        title = CharField(required=False)

    class _Classes:
        simple = SimpleTagMeForm
        mixed = MixedFieldForm

    return _Classes


class AllFieldsForm(AllFieldsTagMeModelFormMixin, Form):
    """Form that dynamically creates fields for all tagged models."""

    pass


# =============================================================================
# TagMeModelFormMixin.__init__
# =============================================================================


@pytest.mark.django_db
class TestTagMeModelFormMixinInit:
    """Kwarg extraction and cooperative user sharing."""

    def test_extracts_user_from_kwargs(self, form_classes):
        user = User(username="testuser")
        form = form_classes.simple(user=user)

        assert form.user == user

    def test_extracts_model_metadata_from_kwargs(self, form_classes):
        user = User(username="testuser")
        form = form_classes.simple(
            user=user,
            model_obj=TaggedFieldTestModel,
            model_verbose_name="Tagged Field Test Model",
            model_name="TaggedFieldTestModel",
        )

        assert form.model_obj == TaggedFieldTestModel
        assert form.model_verbose_name == "Tagged Field Test Model"
        assert form.model_name == "TaggedFieldTestModel"

    def test_defaults_to_none_when_kwargs_missing(self, form_classes):
        form = form_classes.simple()

        assert form.user is None
        assert form.model_obj is None
        assert form.model_verbose_name is None
        assert form.model_name is None

    def test_cooperative_user_sharing(self, form_classes):
        """If another mixin already set self.user, TagMeModelFormMixin uses it.

        Covers line 105: user = self.user (hasattr True branch).
        """
        user_a = User(username="first_mixin_user")

        SimpleForm = form_classes.simple
        form = SimpleForm.__new__(SimpleForm)
        form.user = user_a
        SimpleForm.__init__(form)

        assert form.user == user_a

    def test_unknown_kwargs_not_passed_to_form(self, form_classes):
        """TagMe kwargs are popped, so Form.__init__ doesn't see them."""
        user = User(username="testuser")
        form = form_classes.simple(
            user=user,
            model_obj=TaggedFieldTestModel,
            model_verbose_name="test",
            model_name="test",
        )
        assert isinstance(form, Form)


# =============================================================================
# TagMeModelFormMixin._configure_tagme_widgets
# =============================================================================


@pytest.mark.django_db
class TestConfigureTagmeWidgets:
    """_configure_tagme_widgets: sets widget attrs on TagMeCharField fields.

    Covers lines 150-163: the loop that iterates form fields and configures
    TagMeCharField widgets with user/css_class/field_name attrs.
    """

    def test_sets_user_on_tagme_widget(self, form_classes):
        user = User(username="widgetuser")
        form = form_classes.simple(user=user)

        attrs = form.fields["my_tags"].widget.attrs
        assert attrs["user"] == user
        assert attrs["field_name"] == "my_tags"

    def test_skips_non_tagme_fields(self, form_classes):
        user = User(username="widgetuser")
        form = form_classes.mixed(user=user)

        # TagMeCharField gets user
        assert form.fields["tags"].widget.attrs.get("user") == user

        # Regular CharField is untouched
        assert "user" not in form.fields["title"].widget.attrs

    def test_skips_configuration_when_no_user(self, form_classes):
        form = form_classes.simple()

        # Widget should not have user attr injected
        assert "user" not in form.fields["my_tags"].widget.attrs

    def test_sets_css_class_attr(self, form_classes):
        user = User(username="cssuser")
        form = form_classes.simple(user=user)

        attrs = form.fields["my_tags"].widget.attrs
        assert "css_class" in attrs

    def test_configure_called_directly(self, form_classes):
        """Call _configure_tagme_widgets explicitly for line coverage.

        This ensures the loop body is traced even if dynamic class
        definitions confuse the coverage tool.
        """
        user = User(username="directcall")
        form = form_classes.simple(user=user)

        # Reset attrs to verify re-configuration works
        form.fields["my_tags"].widget.attrs.pop("user", None)
        form.fields["my_tags"].widget.attrs.pop("field_name", None)

        form._configure_tagme_widgets()

        attrs = form.fields["my_tags"].widget.attrs
        assert attrs["user"] == user
        assert attrs["field_name"] == "my_tags"
        assert attrs["css_class"] == ""

    def test_debug_logging_when_enabled(self, form_classes):
        """Covers line 170: debug logging when _debug_widget_config is set."""
        user = User(username="debuguser")
        form = form_classes.simple(user=user)
        form._debug_widget_config = True

        with patch("tag_me.forms.mixins.logger") as mock_logger:
            form._configure_tagme_widgets()

            assert mock_logger.debug.called
            # Should log per-widget and summary
            assert mock_logger.debug.call_count >= 2


# =============================================================================
# AllFieldsTagMeModelFormMixin.__init__
# =============================================================================


@pytest.mark.django_db
class TestAllFieldsFormMixinInit:
    """User requirement and cooperative user sharing.

    Covers lines 257-275: __init__ hasattr branch and user validation.
    """

    def test_raises_when_user_is_none(self):
        with pytest.raises(ObjectDoesNotExist, match="User is required"):
            AllFieldsForm()

    def test_raises_when_user_kwarg_missing(self):
        with pytest.raises(ObjectDoesNotExist, match="User is required"):
            AllFieldsForm(user=None)

    def test_accepts_valid_user(self, test_user):
        form = AllFieldsForm(user=test_user)
        assert form.user == test_user

    def test_cooperative_user_sharing(self, test_user):
        """If another mixin already set self.user, AllFieldsForm uses it.

        Covers lines 257-262: hasattr(self, 'user') True branch.
        """
        form = AllFieldsForm.__new__(AllFieldsForm)
        form.user = test_user
        # No 'user' in kwargs — already popped by first mixin
        AllFieldsForm.__init__(form)

        assert form.user == test_user


# =============================================================================
# AllFieldsTagMeModelFormMixin._create_dynamic_tagme_fields
# =============================================================================


@pytest.mark.django_db
class TestDynamicFieldCreation:
    """_create_dynamic_tagme_fields: builds fields from TaggedFieldModel + UserTag.

    Covers lines 305-362: the full dynamic field creation method including
    TaggedFieldModel query, UserTag prefetch, field creation loop, and
    ObjectDoesNotExist handling.
    """

    @pytest.fixture
    def dynamic_setup(self, test_user, tagged_field_factory, user_tag_factory):
        """Create a TaggedFieldModel + UserTag pair for dynamic field tests."""
        tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="dynamic_test_field",
            model_name="TaggedFieldTestModel",
            model_verbose_name="Tagged Field Test Model",
            field_verbose_name="Dynamic Test Field",
            tag_type="user",
        )
        ut = user_tag_factory(
            user=test_user,
            tagged_field=tfm,
            tags="alpha,beta,gamma",
            field_verbose_name="Dynamic Test Field",
        )
        return {"user": test_user, "tfm": tfm, "ut": ut}

    def test_creates_field_for_tagged_model(self, dynamic_setup):
        form = AllFieldsForm(user=dynamic_setup["user"])

        assert "dynamic_test_field" in form.fields

    def test_field_has_correct_label(self, dynamic_setup):
        form = AllFieldsForm(user=dynamic_setup["user"])
        field = form.fields["dynamic_test_field"]

        assert field.label == "Dynamic Test Field"

    def test_field_is_not_required(self, dynamic_setup):
        form = AllFieldsForm(user=dynamic_setup["user"])
        field = form.fields["dynamic_test_field"]

        assert field.required is False

    def test_widget_has_user_and_tag_string(self, dynamic_setup):
        form = AllFieldsForm(user=dynamic_setup["user"])
        widget_attrs = form.fields["dynamic_test_field"].widget.attrs

        assert widget_attrs["user"] == dynamic_setup["user"]
        assert widget_attrs["all_tag_fields_tag_string"] == "alpha,beta,gamma"

    def test_widget_has_all_fields_mixin_attrs(self, dynamic_setup):
        """Verify all widget attrs set in _create_dynamic_tagme_fields."""
        form = AllFieldsForm(user=dynamic_setup["user"])
        widget_attrs = form.fields["dynamic_test_field"].widget.attrs

        assert widget_attrs["all_tag_fields_mixin"] is True
        assert widget_attrs["display_all_tags"] is False
        assert widget_attrs["field_name"] == "dynamic_test_field"

    def test_skips_field_when_user_tag_missing(self, test_user, tagged_field_factory):
        """TaggedFieldModel exists but no UserTag — field is not created.

        Covers the ObjectDoesNotExist except branch in _create_dynamic_tagme_fields.
        """
        tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="orphan_field",
            model_name="TaggedFieldTestModel",
            tag_type="user",
        )

        form = AllFieldsForm(user=test_user)

        assert "orphan_field" not in form.fields

    def test_only_creates_fields_for_user_tag_type(
        self, test_user, tagged_field_factory
    ):
        """System-type TaggedFieldModels should not appear as dynamic fields."""
        tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="system_only_field",
            model_name="TaggedFieldTestModel",
            tag_type="system",
        )

        form = AllFieldsForm(user=test_user)

        assert "system_only_field" not in form.fields

    def test_create_dynamic_fields_called_directly(self, dynamic_setup):
        """Call _create_dynamic_tagme_fields explicitly for line coverage.

        This ensures lines 305-362 are traced even if __init__ confuses
        the coverage tool with cooperative inheritance.
        """
        form = AllFieldsForm(user=dynamic_setup["user"])

        # Clear dynamically created fields
        form.fields.pop("dynamic_test_field", None)

        # Call directly
        form._create_dynamic_tagme_fields()

        assert "dynamic_test_field" in form.fields
        widget_attrs = form.fields["dynamic_test_field"].widget.attrs
        assert widget_attrs["user"] == dynamic_setup["user"]

    def test_multiple_tagged_fields_create_multiple_form_fields(
        self, test_user, tagged_field_factory, user_tag_factory
    ):
        """Multiple TaggedFieldModels each get their own form field."""
        ct, _ = ContentType.objects.get_or_create(
            app_label="tests", model="multifieldtest"
        )
        tfm1 = tagged_field_factory(
            content_type=ct,
            field_name="multi_field_a",
            model_name="MultiFieldTest",
            tag_type="user",
        )
        tfm2 = tagged_field_factory(
            content_type=ct,
            field_name="multi_field_b",
            model_name="MultiFieldTest",
            tag_type="user",
        )
        user_tag_factory(user=test_user, tagged_field=tfm1, tags="a1,a2")
        user_tag_factory(user=test_user, tagged_field=tfm2, tags="b1,b2")

        form = AllFieldsForm(user=test_user)

        assert "multi_field_a" in form.fields
        assert "multi_field_b" in form.fields

    def test_debug_logging_when_enabled(self, dynamic_setup):
        """Covers debug logging in _create_dynamic_tagme_fields."""
        form = AllFieldsForm(user=dynamic_setup["user"])
        form._debug_widget_config = True

        # Clear and re-create to trigger logging
        form.fields.pop("dynamic_test_field", None)

        with patch("tag_me.forms.mixins.logger") as mock_logger:
            form._create_dynamic_tagme_fields()

            assert mock_logger.debug.called


# =============================================================================
# FK Lookup Resilience (absorbed from test_fk_migration.py)
# =============================================================================


@pytest.mark.django_db
class TestAllFieldsFKIntegration:
    """AllFieldsTagMeModelFormMixin uses FK lookup, surviving model renames.

    Absorbed from test_fk_migration.py TestFormMixinFKIntegration.
    Uses a fake ContentType to avoid collision with auto-registered fields.
    """

    @pytest.fixture
    def fk_setup(self, test_user_factory, tagged_field_factory):
        """Create an isolated TaggedFieldModel + UserTag for FK tests.

        Uses a fake ContentType so the field_name doesn't collide with
        real registered fields on TaggedFieldTestModel.
        """
        ct, _ = ContentType.objects.get_or_create(
            app_label="tests", model="fkintegrationfake"
        )
        user = test_user_factory(username="fkuser")
        tfm = tagged_field_factory(
            content_type=ct,
            field_name="fk_test_field",
            model_name="FKIntegrationFake",
            model_verbose_name="FK Integration Fake",
            field_verbose_name="FK Test Field",
        )
        ut = UserTag.objects.create(
            user=user,
            tagged_field=tfm,
            model_name="FKIntegrationFake",
            model_verbose_name="FK Integration Fake",
            field_name="fk_test_field",
            field_verbose_name="FK Test Field",
            tags="mixin,test,tags",
        )
        return {"user": user, "tfm": tfm, "ut": ut}

    def test_finds_user_tag_by_fk(self, fk_setup):
        form = AllFieldsForm(user=fk_setup["user"])

        assert "fk_test_field" in form.fields

    def test_works_with_stale_model_name(self, fk_setup):
        """FK lookup still works even if model_name was updated."""
        fk_setup["tfm"].model_name = "OldModelName"
        fk_setup["tfm"].save()
        fk_setup["ut"].model_name = "OldModelName"
        fk_setup["ut"].save(sync_tags_save=True)

        form = AllFieldsForm(user=fk_setup["user"])

        assert "fk_test_field" in form.fields
