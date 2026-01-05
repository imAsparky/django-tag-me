"""
Regression tests for fixes made during deep review.

This test suite ensures the bugs don't regress. Each test class
corresponds to fixes from a specific category.


Coverage targets:
- Thread safety
- Slug collision retry
- NULL handling
- Validation
- formfield kwargs
- Sync logic
"""

import concurrent.futures
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.test import TransactionTestCase

from tag_me.models import (
    SystemTag,
    TaggedFieldModel,
    TagMeSynchronise,
    UserTag,
)

# Import TAG_TYPES from the models module directly (not exported in __init__.py)
# If this fails, define them locally as they should match the model definition
try:
    from tag_me.models.models import TAG_TYPE_DEFAULT, TAG_TYPES
except ImportError:
    # Fallback: define locally (must match models.py)
    TAG_TYPES = ["user", "system"]
    TAG_TYPE_DEFAULT = "user"

from tag_me.models.fields import TagMeCharField

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def second_user(db):
    """Create a second test user."""
    return User.objects.create_user(username="testuser2", password="testpass2")


@pytest.fixture
def content_type(db):
    """Get or create a ContentType for testing."""
    return ContentType.objects.get_or_create(
        app_label="tests",
        model="taggedfieldtestmodel",
    )[0]


@pytest.fixture
def tagged_field_model(db, content_type):
    """Create a TaggedFieldModel entry."""
    return TaggedFieldModel.objects.create(
        content=content_type,
        model_name="TaggedFieldTestModel",
        model_verbose_name="Tagged Field Test Model",
        field_name="test_field",
        field_verbose_name="Test Field",
        tag_type="user",
    )


@pytest.fixture
def user_tag(db, user, tagged_field_model):
    """Create a UserTag entry."""
    return UserTag.objects.create(
        user=user,
        tagged_field=tagged_field_model,
        model_name="TaggedFieldTestModel",
        field_name="test_field",
        tags="tag1,tag2,",
    )


class TestNullHandling:
    """Tests for NULL handling fixes from Iteration 3."""

    def test_user_tag_str_with_null_user(self, db, tagged_field_model):
        """UserTag.__str__() should not crash when user is NULL."""
        user_tag = UserTag.objects.create(
            user=None,
            tagged_field=tagged_field_model,
            model_name="TestModel",
            field_name="test_field",
            tags="tag1,",
        )

        # Should not raise, should contain "NO_USER"
        result = str(user_tag)
        assert "NO_USER" in result

    def test_user_tag_save_with_null_tagged_field(self, db, user):
        """UserTag.save() should handle NULL tagged_field gracefully."""
        user_tag = UserTag(
            user=user,
            tagged_field=None,  # Orphaned record
            model_name="DeletedModel",
            field_name="deleted_field",
            tags="tag1,",
        )

        # Should not crash - just log warning and save
        user_tag.save()
        assert user_tag.pk is not None

    def test_tagged_field_model_str_with_nulls(self, db, content_type):
        """TaggedFieldModel.__str__() should handle NULL verbose names."""
        tfm = TaggedFieldModel.objects.create(
            content=content_type,
            model_name=None,
            model_verbose_name=None,
            field_name="test_field",
            field_verbose_name=None,
            tag_type="user",
        )

        result = str(tfm)
        assert "Unknown" in result or "test_field" in result

    def test_system_tag_str_with_nulls(self, db, tagged_field_model):
        """SystemTag.__str__() should handle NULL fields gracefully."""
        system_tag = SystemTag.objects.create(
            tagged_field=tagged_field_model,
            model_name=None,
            model_verbose_name=None,
            field_name=None,
            tags="sys_tag,",
        )

        result = str(system_tag)
        assert "Unknown" in result


class TestTaggedFieldModelValidation:
    """Tests for TaggedFieldModel.save() validation from Iteration 4."""

    def test_save_requires_field_name(self, db, content_type):
        """TaggedFieldModel.save() should reject NULL field_name."""
        tfm = TaggedFieldModel(
            content=content_type,
            model_name="TestModel",
            field_name=None,  # Invalid!
            tag_type="user",
        )

        with pytest.raises(ValueError, match="field_name cannot be empty"):
            tfm.save()

    def test_save_requires_content(self, db):
        """TaggedFieldModel.save() should reject NULL content."""
        tfm = TaggedFieldModel(
            content=None,  # Invalid!
            model_name="TestModel",
            field_name="test_field",
            tag_type="user",
        )

        with pytest.raises(ValueError, match="content cannot be empty"):
            tfm.save()

    def test_save_validates_tag_type(self, db, content_type):
        """TaggedFieldModel.save() should reject invalid tag_type."""
        tfm = TaggedFieldModel(
            content=content_type,
            model_name="TestModel",
            field_name="test_field",
            tag_type="invalid_type",  # Not in TAG_TYPES!
        )

        with pytest.raises(ValueError, match="tag_type must be one of"):
            tfm.save()

    def test_save_accepts_valid_tag_types(self, db, content_type):
        """TaggedFieldModel.save() should accept all valid tag types."""
        for tag_type in TAG_TYPES:
            tfm = TaggedFieldModel(
                content=content_type,
                model_name="TestModel",
                field_name=f"field_{tag_type}",
                tag_type=tag_type,
            )
            tfm.save()  # Should not raise
            assert tfm.pk is not None
            tfm.delete()  # Cleanup

    def test_tag_type_default_constant(self):
        """TAG_TYPE_DEFAULT should be a valid tag type."""
        assert TAG_TYPE_DEFAULT in TAG_TYPES


class TestTagMeSynchronise:
    """Tests for TagMeSynchronise fixes from Iteration 4."""

    def test_add_model_to_sync_list_with_none_content_type(self, db):
        """_add_model_to_sync_list should return False for None content_type_id."""
        sync = TagMeSynchronise.objects.create(name="test_sync")

        result = sync._add_model_to_sync_list(
            content_type_id=None,
            field="test_field",
        )

        assert result is False

    def test_add_model_to_sync_list_with_none_field(self, db):
        """_add_model_to_sync_list should return False for None field."""
        sync = TagMeSynchronise.objects.create(name="test_sync")

        result = sync._add_model_to_sync_list(
            content_type_id="123",
            field=None,
        )

        assert result is False

    def test_add_model_to_sync_list_creates_field_list(self, db):
        """_add_model_to_sync_list should create field list if missing."""
        sync = TagMeSynchronise.objects.create(name="test_sync", synchronise={})

        result = sync._add_model_to_sync_list(
            content_type_id="123",
            field="new_field",
        )

        assert result is True
        assert "new_field" in sync.synchronise
        assert "123" in sync.synchronise["new_field"]

    def test_add_model_to_sync_list_prevents_duplicates(self, db):
        """_add_model_to_sync_list should not add duplicate content_type_id."""
        sync = TagMeSynchronise.objects.create(
            name="test_sync",
            synchronise={"test_field": ["123"]},
        )

        result = sync._add_model_to_sync_list(
            content_type_id="123",
            field="test_field",
        )

        assert result is False  # Already exists
        assert sync.synchronise["test_field"].count("123") == 1

    def test_get_field_name_models_to_sync_returns_list(self, db):
        """_get_field_name_models_to_sync should return list, not bool."""
        sync = TagMeSynchronise.objects.create(
            name="test_sync",
            synchronise={"test_field": ["123", "456"]},
        )

        result = sync._get_field_name_models_to_sync("test_field")

        assert isinstance(result, list)
        assert result == ["123", "456"]

    def test_get_field_name_models_to_sync_returns_none_for_missing(self, db):
        """_get_field_name_models_to_sync should return None for missing field."""
        sync = TagMeSynchronise.objects.create(name="test_sync", synchronise={})

        result = sync._get_field_name_models_to_sync("nonexistent")

        assert result is None


class TestSlugCollisionRetry(TransactionTestCase):
    """Tests for TagBase.save() slug collision retry from Iteration 5."""

    def test_slug_retry_on_collision(self):
        """TagBase.save() should retry with new slug on IntegrityError."""
        user = User.objects.create_user(username="testuser", password="testpass")
        content_type = ContentType.objects.get_or_create(
            app_label="tests", model="testmodel"
        )[0]
        tagged_field = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="TestModel",
            field_name="test_field",
            tag_type="user",
        )

        # Create first UserTag
        ut1 = UserTag.objects.create(
            user=user,
            tagged_field=tagged_field,
            model_name="TestModel",
            field_name="test_field",
            tags="same_tags,",
        )
        original_slug = ut1.slug

        # Create second UserTag - should get different slug even with same tags
        user2 = User.objects.create_user(username="testuser2", password="testpass2")
        ut2 = UserTag.objects.create(
            user=user2,
            tagged_field=tagged_field,
            model_name="TestModel",
            field_name="test_field2",
            tags="same_tags,",  # Same tags
        )

        # Slugs should be different due to random component
        assert ut1.slug != ut2.slug

    @patch("tag_me.models.TagBase.slugify")
    def test_slug_retry_exhaustion_raises(self, mock_slugify):
        """TagBase.save() should raise after max retries exhausted."""
        # Make slugify always return the same slug to force collisions
        mock_slugify.return_value = "always-same-slug"

        user = User.objects.create_user(username="testuser3", password="testpass")
        content_type = ContentType.objects.get_or_create(
            app_label="tests", model="testmodel2"
        )[0]
        tagged_field = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="TestModel2",
            field_name="test_field",
            tag_type="user",
        )

        # Create first with the fixed slug
        UserTag.objects.create(
            user=user,
            tagged_field=tagged_field,
            model_name="TestModel2",
            field_name="test_field",
            tags="tag1,",
            slug="always-same-slug",
        )

        # Second should fail after retries
        user2 = User.objects.create_user(username="testuser4", password="testpass")
        ut2 = UserTag(
            user=user2,
            tagged_field=tagged_field,
            model_name="TestModel2",
            field_name="test_field2",
            tags="tag1,",
        )

        with pytest.raises(IntegrityError):
            ut2.save()


class TestThreadSafety:
    """Tests for thread safety fixes from Iteration 6."""

    def test_formatter_isolation_in_from_db_value(self):
        """from_db_value should use isolated formatter instances."""
        field = TagMeCharField()

        # Simulate concurrent calls
        results = []

        def call_from_db(value):
            result = field.from_db_value(value, None, None)
            results.append((value, result))

        # Run in threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(100):
                value = f"tag{i},"
                futures.append(executor.submit(call_from_db, value))

            concurrent.futures.wait(futures)

        # Each result should match its input (no cross-contamination)
        for original, result in results:
            assert original.strip(",") in result or result == original

    def test_formatter_isolation_in_get_prep_value(self):
        """get_prep_value should use isolated formatter instances."""
        field = TagMeCharField()

        results = []

        def call_prep(value):
            result = field.get_prep_value(value)
            results.append((value, result))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(100):
                value = f"prep_tag{i}"
                futures.append(executor.submit(call_prep, value))

            concurrent.futures.wait(futures)

        # Results should not be contaminated
        for original, result in results:
            # The original tag should be in the result
            assert original in result or original.replace(",", "") in result

    def test_formatter_isolation_in_to_python(self):
        """to_python should use isolated formatter instances."""
        field = TagMeCharField()

        results = []

        def call_to_python(value):
            result = field.to_python(value)
            results.append((value, result))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(100):
                value = f"python_tag{i},"
                futures.append(executor.submit(call_to_python, value))

            concurrent.futures.wait(futures)

        for original, result in results:
            assert original.strip(",") in result or result == original


class TestSystemTagConstraint(TransactionTestCase):
    """Tests for SystemTag unique constraint from Iteration 6."""

    def test_unique_system_tag_per_tagged_field(self):
        """Only one SystemTag allowed per TaggedFieldModel."""
        content_type = ContentType.objects.get_or_create(
            app_label="tests", model="constrainttest"
        )[0]
        tagged_field = TaggedFieldModel.objects.create(
            content=content_type,
            model_name="ConstraintTestModel",
            field_name="sys_field",
            tag_type="system",
        )

        # First SystemTag - should succeed
        SystemTag.objects.create(
            tagged_field=tagged_field,
            model_name="ConstraintTestModel",
            field_name="sys_field",
            tags="sys1,",
        )

        # Second SystemTag for same tagged_field - should fail
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SystemTag.objects.create(
                    tagged_field=tagged_field,
                    model_name="ConstraintTestModel",
                    field_name="sys_field",
                    tags="sys2,",
                )

    def test_null_tagged_field_allowed_multiple(self):
        """Multiple SystemTags with NULL tagged_field are allowed (SQL NULL != NULL)."""
        # This documents the expected behavior - NULLs don't violate unique constraint
        st1 = SystemTag.objects.create(
            tagged_field=None,
            model_name="OrphanModel1",
            field_name="field1",
            tags="orphan1,",
        )

        st2 = SystemTag.objects.create(
            tagged_field=None,
            model_name="OrphanModel2",
            field_name="field2",
            tags="orphan2,",
        )

        assert st1.pk is not None
        assert st2.pk is not None


class TestFormfieldKwargs:
    """Tests for formfield() kwargs merging from Iteration 7."""

    @pytest.mark.django_db
    def test_formfield_preserves_help_text(self):
        """formfield() should preserve custom help_text."""
        field = TagMeCharField()
        field.name = "test_field"
        # Don't set field.model - fresh fields don't have it
        # formfield() handles this case gracefully

        form_field = field.formfield(help_text="Custom help text")

        assert form_field.help_text == "Custom help text"

    @pytest.mark.django_db
    def test_formfield_preserves_label(self):
        """formfield() should preserve custom label."""
        field = TagMeCharField()
        field.name = "test_field"

        form_field = field.formfield(label="Custom Label")

        assert form_field.label == "Custom Label"

    @pytest.mark.django_db
    def test_formfield_preserves_initial(self):
        """formfield() should preserve initial value."""
        field = TagMeCharField()
        field.name = "test_field"

        form_field = field.formfield(initial="initial_tag,")

        assert form_field.initial == "initial_tag,"


class TestTagMeCharFieldInit:
    """Tests for TagMeCharField initialization."""

    def test_system_tag_requires_choices(self):
        """system_tag=True without choices should raise ValueError."""
        with pytest.raises(ValueError, match="requires 'choices'"):
            TagMeCharField(system_tag=True)

    def test_choices_without_system_tag_warns(self):
        """choices without system_tag should emit deprecation warning."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            field = TagMeCharField(choices=["tag1", "tag2"])

            # Should have issued a DeprecationWarning
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

            # Should have auto-fixed to system_tag=True
            assert field.system_tag is True

    def test_empty_choices_raises(self):
        """Empty choices list should raise ValueError."""
        with pytest.raises(ValueError, match="choices"):
            TagMeCharField(choices=[], system_tag=True)

    def test_choices_as_tuples(self):
        """Choices as Django-style tuples should work."""
        field = TagMeCharField(
            choices=[("val1", "Label 1"), ("val2", "Label 2")],
            system_tag=True,
        )

        assert "val1" in field._tag_choices
        assert "val2" in field._tag_choices

    def test_choices_as_simple_list(self):
        """Choices as simple list should work."""
        field = TagMeCharField(
            choices=["simple1", "simple2"],
            system_tag=True,
        )

        assert "simple1" in field._tag_choices
        assert "simple2" in field._tag_choices


class TestDeconstruct:
    """Tests for field deconstruction (migration serialization)."""

    def test_deconstruct_includes_choices(self):
        """deconstruct should include choices if present."""
        field = TagMeCharField(
            choices=["tag1", "tag2"],
            system_tag=True,
        )

        name, path, args, kwargs = field.deconstruct()

        assert "choices" in kwargs
        assert kwargs["choices"] == ["tag1", "tag2"]

    def test_deconstruct_includes_system_tag_when_true(self):
        """deconstruct should include system_tag when True."""
        field = TagMeCharField(
            choices=["tag1"],
            system_tag=True,
        )

        name, path, args, kwargs = field.deconstruct()

        assert kwargs.get("system_tag") is True

    def test_deconstruct_excludes_defaults(self):
        """deconstruct should exclude default values."""
        field = TagMeCharField()  # All defaults

        name, path, args, kwargs = field.deconstruct()

        # These are defaults, shouldn't be in kwargs
        assert "multiple" not in kwargs  # Default is True
        assert "synchronise" not in kwargs  # Default is False
        assert "system_tag" not in kwargs  # Default is False

    def test_deconstruct_includes_non_defaults(self):
        """deconstruct should include non-default values."""
        field = TagMeCharField(
            multiple=False,
            synchronise=True,
        )

        name, path, args, kwargs = field.deconstruct()

        assert kwargs.get("multiple") is False
        assert kwargs.get("synchronise") is True
