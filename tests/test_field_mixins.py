from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.forms import Form
from django.test import RequestFactory
from django.views.generic import FormView

from tag_me.forms.mixins import TagMeModelFormMixin
from tag_me.views.mixins import TagMeViewMixin
from tests.models import TaggedFieldTestModel


@pytest.fixture
def mock_logger():
    """Mock the structlog logger for testing"""
    with patch("tag_me.views.mixins.logger") as mock:
        yield mock


class TestTagMeForm(TagMeModelFormMixin, Form):
    """Valid form for testing"""

    pass


class InvalidTestForm(Form):
    """Invalid form for testing"""

    pass


class TestView(TagMeViewMixin, FormView):
    """Test view class"""

    model = TaggedFieldTestModel


@pytest.fixture
def view_instance():
    view = TestView()
    view.request = RequestFactory().get("/")
    view.request.user = User(username="testuser")
    return view


def test_get_form_with_valid_form(view_instance):
    """Test get_form with a valid form class inheriting from TagMeModelFormMixin"""
    form = view_instance.get_form(TestTagMeForm)

    assert isinstance(form, TestTagMeForm)
    assert form.user == view_instance.request.user
    assert form.model_verbose_name == (TaggedFieldTestModel._meta.verbose_name,)
    assert form.model_obj == TaggedFieldTestModel


def test_get_form_with_invalid_form(view_instance):
    """Test get_form raises ImproperlyConfigured when form doesn't inherit from TagMeModelFormMixin"""
    with pytest.raises(ImproperlyConfigured) as exc_info:
        view_instance.get_form(InvalidTestForm)

    assert "must inherit from TagMeModelFormMixin" in str(exc_info.value)


def test_get_form_with_existing_user(view_instance):
    """Test get_form when user is already in form_kwargs"""
    existing_user = User(username="existing_user")
    view_instance.get_form_kwargs = lambda: {"user": existing_user}

    form = view_instance.get_form(TestTagMeForm)
    assert form.user == existing_user


@pytest.mark.django_db
def test_get_initial(view_instance):
    """Test get_initial returns correct initial data"""
    initial = view_instance.get_initial()

    assert initial["user"] == view_instance.request.user
    assert isinstance(initial["content_type"], ContentType)
    assert initial["model_verbose_name"] == TaggedFieldTestModel._meta.verbose_name


@pytest.mark.django_db
def test_get_initial_content_type(view_instance):
    """Test get_initial creates correct content type"""
    initial = view_instance.get_initial()
    content_type = initial["content_type"]

    assert isinstance(content_type, ContentType)
    expected_content_type = ContentType.objects.get_for_model(
        TaggedFieldTestModel, for_concrete_model=True
    )
    assert content_type.model == expected_content_type.model


def test_get_form_logs_error_for_invalid_form(view_instance, mock_logger):
    """Test that an error is logged when form doesn't inherit from TagMeModelFormMixin"""

    with pytest.raises(ImproperlyConfigured):
        view_instance.get_form(InvalidTestForm)

    mock_logger.error.assert_called_once()

    # Check specific structlog call structure
    call_kwargs = mock_logger.error.call_args.kwargs
    assert call_kwargs["event"] == "get_form"
    assert "form_class" in call_kwargs["data"]


def test_get_form_without_form_class(view_instance, mock_logger):
    """Test get_form when no form_class is provided"""
    view_instance.get_form_class = lambda: InvalidTestForm

    with pytest.raises(ImproperlyConfigured):
        view_instance.get_form(form_class=None)

    mock_logger.error.assert_called_once()
    assert "get_form" in str(mock_logger.error.call_args)
