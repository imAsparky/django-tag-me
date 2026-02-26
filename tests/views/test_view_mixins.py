"""
Tests for tag-me view mixins.

Covers:
    - TagMeViewMixin.get_form: validation, user injection, model metadata
    - TagMeViewMixin.get_initial: user, content_type, model_verbose_name
    - Error logging for invalid form classes

Run with: pytest tests/test_view_mixins.py -v
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.forms import Form
from django.test import RequestFactory
from django.views.generic import FormView

from tag_me.forms.mixins import TagMeModelFormMixin
from tag_me.views.mixins import TagMeViewMixin
from tests.models import TaggedFieldTestModel

User = get_user_model()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class ValidTagMeForm(TagMeModelFormMixin, Form):
    """Form that correctly inherits from TagMeModelFormMixin."""

    pass


class InvalidForm(Form):
    """Form missing the required TagMeModelFormMixin base class."""

    pass


class SampleView(TagMeViewMixin, FormView):
    """Minimal view wired to TaggedFieldTestModel."""

    model = TaggedFieldTestModel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_logger():
    """Mock the structlog logger used by the view mixin."""
    with patch("tag_me.views.mixins.logger") as mock:
        yield mock


@pytest.fixture
def view_instance():
    """A SampleView with a fake GET request and unsaved user."""
    view = SampleView()
    view.request = RequestFactory().get("/")
    view.request.user = User(username="testuser")
    return view


# ---------------------------------------------------------------------------
# get_form
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetForm:
    """TagMeViewMixin.get_form: validates form class and injects kwargs."""

    def test_returns_form_with_user_and_model_metadata(self, view_instance):
        form = view_instance.get_form(ValidTagMeForm)

        assert isinstance(form, ValidTagMeForm)
        assert form.user == view_instance.request.user
        assert form.model_verbose_name == (TaggedFieldTestModel._meta.verbose_name,)
        assert form.model_obj == TaggedFieldTestModel

    def test_raises_for_form_without_mixin(self, view_instance):
        with pytest.raises(ImproperlyConfigured) as exc_info:
            view_instance.get_form(InvalidForm)

        assert "must inherit from TagMeModelFormMixin" in str(exc_info.value)

    def test_preserves_existing_user_in_kwargs(self, view_instance):
        """If another mixin already injected 'user', get_form keeps it."""
        existing_user = User(username="existing_user")
        view_instance.get_form_kwargs = lambda: {"user": existing_user}

        form = view_instance.get_form(ValidTagMeForm)

        assert form.user == existing_user

    def test_falls_back_to_get_form_class_when_none(self, view_instance, mock_logger):
        """When form_class=None, delegates to get_form_class()."""
        view_instance.get_form_class = lambda: InvalidForm

        with pytest.raises(ImproperlyConfigured):
            view_instance.get_form(form_class=None)

        mock_logger.error.assert_called_once()
        assert "get_form" in str(mock_logger.error.call_args)


# ---------------------------------------------------------------------------
# get_initial
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetInitial:
    """TagMeViewMixin.get_initial: returns user, content_type, verbose_name."""

    def test_returns_required_keys(self, view_instance):
        initial = view_instance.get_initial()

        assert initial["user"] == view_instance.request.user
        assert isinstance(initial["content_type"], ContentType)
        assert initial["model_verbose_name"] == TaggedFieldTestModel._meta.verbose_name

    def test_content_type_matches_model(self, view_instance):
        initial = view_instance.get_initial()
        expected_ct = ContentType.objects.get_for_model(
            TaggedFieldTestModel, for_concrete_model=True
        )

        assert initial["content_type"].model == expected_ct.model


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestViewMixinLogging:
    """Structured logging for error paths."""

    def test_logs_error_for_invalid_form(self, view_instance, mock_logger):
        with pytest.raises(ImproperlyConfigured):
            view_instance.get_form(InvalidForm)

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args.kwargs
        assert call_kwargs["event"] == "get_form"
        assert "form_class" in call_kwargs["data"]
