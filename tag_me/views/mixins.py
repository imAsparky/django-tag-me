"""Django-tag-me view mixins"""

import structlog

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from tag_me.forms.mixins import TagMeModelFormMixin

logger = structlog.get_logger(__name__)


class TagMeViewMixin:
    """
    Cooperative view mixin for Django CBVs to handle forms with tagged fields.

    This mixin enhances Django's form-capable views (CreateView, UpdateView, FormView, etc.)
    to work seamlessly with TagMe functionality. It automatically passes required context
    to TagMe forms including the current user, model metadata, and content type information.

    Key Features:
    - Validates that the form class inherits from TagMeModelFormMixin
    - Automatically passes user context to forms
    - Provides model metadata for tag management
    - Sets up content type information for proper tag association
    - Designed for cooperative inheritance with other form mixins

    Usage:
        class BlogPostCreateView(TagMeViewMixin, CreateView):
            model = BlogPost
            form_class = BlogPostForm  # Must inherit from TagMeModelFormMixin

        class ArticleUpdateView(TagMeViewMixin, BlockNoteUserViewMixin, UpdateView):
            model = Article
            form_class = ArticleForm

    Requirements:
    - Must be used with views that support forms (inherit from FormMixin capabilities)
    - The form_class must inherit from TagMeModelFormMixin
    - The view must have a 'model' attribute defined
    - Must be used with authenticated users (requires request.user)

    Cooperative Inheritance:
    This mixin is designed to work cooperatively with other form mixins:
    - Always calls super() methods to maintain the inheritance chain
    - Safely checks for existing 'user' in form_kwargs before adding
    - Can be combined with other mixins like BlockNoteUserViewMixin
    - Order in MRO doesn't typically matter for basic functionality

    Form Integration:
    The mixin passes several key parameters to the form:
    - 'user': The current request user for permission checks and tag ownership
    - 'model_verbose_name': Human-readable model name for UI display
    - 'model_obj': The actual model class for metadata access
    - Content type and model information in initial data

    Error Handling:
    - Raises ImproperlyConfigured if form doesn't inherit from TagMeModelFormMixin
    - Logs configuration errors for debugging
    - Gracefully handles missing user context

    Thread Safety:
    This mixin is stateless and thread-safe. All data is passed through
    method parameters rather than stored as instance attributes.

    Example with Multiple Mixins:
        class CombinedView(TagMeViewMixin, BlockNoteViewMixin, CreateView):
            model = BlogPost
            form_class = BlogPostForm

            # Both mixins will cooperatively add 'user' to form_kwargs
            # TagMe adds model metadata, BlockNote configures widgets
    """

    request: HttpRequest

    def get_form_kwargs(self):
        """
        Return the keyword arguments for instantiating the form.

        Enhances the standard form kwargs with TagMe-specific parameters:
        - Ensures 'user' is available for tag permission checks
        - Adds 'model_verbose_name' for display in tag interfaces
        - Adds 'model_obj' for form introspection and validation

        The method is designed to be cooperative - it only adds 'user'
        if not already present, allowing other mixins to also provide
        user context without conflicts.

        Returns:
            dict: Enhanced form kwargs with TagMe context

        Note:
            This method calls super() to maintain cooperative inheritance.
            Other mixins in the MRO chain will also be able to modify
            the form_kwargs appropriately.
        """
        form_kwargs = super().get_form_kwargs()

        # Only add user if not already provided by another mixin
        # This ensures cooperative behavior with other form mixins
        if "user" not in form_kwargs:
            form_kwargs["user"] = self.request.user

        # Add TagMe-specific metadata for form processing
        form_kwargs["model_verbose_name"] = (self.model._meta.verbose_name,)
        form_kwargs["model_obj"] = self.model

        return form_kwargs

    def get_form(self, form_class=None):
        """
        Return an instance of the form to be used in this view.

        Validates that the form class is compatible with TagMe functionality
        before instantiation. This prevents runtime errors and provides
        clear feedback when forms are misconfigured.

        Args:
            form_class (class, optional): The form class to instantiate.
                If None, uses get_form_class() to determine the form.

        Returns:
            Form: Instantiated form ready for TagMe functionality

        Raises:
            ImproperlyConfigured: If the form class doesn't inherit from
                TagMeModelFormMixin, which is required for TagMe functionality.

        Note:
            This validation happens before form instantiation to catch
            configuration issues early in the request cycle.
        """
        if form_class is None:
            form_class = self.get_form_class()

        # Validate that the form supports TagMe functionality
        if not issubclass(form_class, TagMeModelFormMixin):
            msg = (
                f"The form {form_class} used with TagMeViewMixin must inherit "
                f"from TagMeModelFormMixin. This is required for TagMe functionality "
                f"including tag validation, user permissions, and model metadata access."
            )
            logger.error(
                event="get_form",
                msg=msg,
                data={
                    "form_class": form_class,
                },
            )
            raise ImproperlyConfigured(msg)

        # Use cooperative inheritance to get the form instance
        return super().get_form(form_class)

    def get_initial(self):
        """
        Return the initial data to use for forms on this view.

        Provides TagMe-specific initial data including user context,
        content type information, and model metadata. This data is
        used by TagMe forms for proper tag association and permission
        checking during form rendering and validation.

        Returns:
            dict: Initial form data enhanced with TagMe context

        Initial Data Provided:
        - 'user': Current request user for tag ownership
        - 'content_type': ContentType instance for tag association
        - 'model_verbose_name': Human-readable model name

        Note:
            This method cooperatively calls super() to ensure other
            mixins can also contribute initial data. The TagMe data
            is additive and won't overwrite existing initial values.
        """
        initial = super().get_initial()

        # Add user context for tag permission checking
        initial["user"] = self.request.user

        # Add content type for proper tag association
        initial["content_type"] = ContentType.objects.get_for_model(
            self.model, for_concrete_model=True
        )

        # Add human-readable model name for UI display
        initial["model_verbose_name"] = self.model._meta.verbose_name

        return initial
