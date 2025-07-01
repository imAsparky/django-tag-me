"""Django-tag-me form mixins"""

import structlog
from typing import Union

from django import forms
from django.core.exceptions import ObjectDoesNotExist

from tag_me.forms.fields import TagMeCharField
from tag_me.models import TaggedFieldModel, UserTag
from tag_me.widgets import TagMeSelectMultipleWidget

logger = structlog.get_logger(__name__)


class TagMeModelFormMixin:
    """
    Cooperative form mixin for Django ModelForms that enhances TagMeCharField fields.

    This mixin provides automatic configuration and behavior for TagMeCharField fields
    within a ModelForm, with support for user-specific customization and cooperative
    inheritance with other form mixins.

    Key Features:
    - Automatically configures TagMeCharField widgets with user context
    - Stores model metadata for tag management and validation
    - Designed for cooperative inheritance with other form mixins
    - Gracefully handles missing user context
    - Thread-safe and stateless design

    Usage:
        class BlogPostForm(TagMeModelFormMixin, forms.ModelForm):
            tags = TagMeCharField()

            class Meta:
                model = BlogPost
                fields = ['title', 'content', 'tags']

        # Combined with other mixins
        class ArticleForm(TagMeModelFormMixin, BlockNoteUserFormMixin, forms.ModelForm):
            content = forms.CharField(widget=BlockNoteWidget())
            tags = TagMeCharField()

            class Meta:
                model = Article
                fields = ['title', 'content', 'tags']

    Form Integration:
    The mixin expects these kwargs from the view:
    - 'user': Current user for tag permissions and ownership
    - 'model_obj': Model class for metadata access
    - 'model_verbose_name': Human-readable model name tuple
    - 'model_name': Optional model name override

    Widget Configuration:
    Automatically enhances TagMeCharField widgets with:
    - User context for permission checking
    - CSS classes for consistent styling
    - Field metadata for widget behavior

    Cooperative Design:
    - Uses shared user extraction pattern for compatibility
    - Stores user reference for other mixins to access
    - Calls super().__init__ appropriately
    - Doesn't interfere with other mixin functionality

    Thread Safety:
    All configuration is done in __init__ and stored as instance
    attributes, making this mixin thread-safe for Django's
    request-response cycle.
    """

    fields: dict[str, Union[TagMeCharField, forms.Field]]

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with TagMe-specific configuration.

        Extracts TagMe-specific parameters from kwargs and configures
        TagMeCharField widgets with proper user context and metadata.
        Uses cooperative inheritance pattern to work with other mixins.

        Args:
            *args: Variable length argument list for parent form
            **kwargs: Keyword arguments including:
                - user: Current user object for tag permissions
                - model_obj: Model class for metadata access
                - model_verbose_name: Human-readable model name tuple
                - model_name: Optional model name override

        Cooperative Behavior:
        - Checks if user was already extracted by another mixin
        - Extracts user from kwargs if not already available
        - Stores extracted values as instance attributes
        - Configures widgets after form initialization

        User Sharing Strategy:
        - First mixin to run extracts user with pop() and stores it
        - Subsequent mixins check for existing self.user attribute
        - This prevents TypeError from unexpected kwargs in Django forms
        """
        # Check if user was already extracted by another mixin
        if hasattr(self, "user"):
            # Another mixin already extracted the user - use that
            user = self.user
        else:
            # First mixin to run - extract user from kwargs
            user = kwargs.pop("user", None)
            self.user = user

        # Extract TagMe-specific parameters
        self.model_obj = kwargs.pop("model_obj", None)
        self.model_verbose_name = kwargs.pop("model_verbose_name", None)
        self.model_name = kwargs.pop("model_name", None)

        # Call parent form initialization
        super().__init__(*args, **kwargs)

        # Configure TagMe widgets after form is initialized
        self._configure_tagme_widgets()

    def _configure_tagme_widgets(self):
        """
        Configure all TagMeCharField widgets with user context and styling.

        Iterates through all form fields and enhances TagMeCharField widgets
        with user context and CSS styling. This method is called automatically
        during form initialization.

        Widget Configuration:
        - Adds user context for permission checking
        - Sets CSS classes for consistent styling
        - Provides field metadata for widget behavior

        Safety Features:
        - Gracefully handles missing user context
        - Only modifies TagMeCharField widgets
        - Uses widget.attrs.update() for safe attribute merging

        Debug Support:
        - Logs widget configuration in development
        - Counts configured widgets for debugging
        """
        if not self.user:
            return

        configured_count = 0

        for field_name, field in self.fields.items():
            if isinstance(field, TagMeCharField):
                # Configure widget with user context and styling
                field.widget.attrs.update(
                    {
                        "css_class": "",  # Default CSS class
                        "user": self.user,  # User context for permissions
                        "field_name": field_name,  # Field identifier
                    }
                )
                configured_count += 1

                # Debug logging in development
                if hasattr(self, "_debug_widget_config"):
                    logger.debug(
                        event="_configure_tagme_widgets",
                        msg=f"✅ Configured TagMe widget '{field_name}' for user {self.user.username}",
                    )

        # Optional debug output
        if configured_count > 0 and hasattr(self, "_debug_widget_config"):
            logger.debug(
                event="_configure_tagme_widgets",
                msg=f"🏷️ Configured {configured_count} TagMe widget(s) for user {self.user.username}",
            )


class AllFieldsTagMeModelFormMixin:
    """
    Cooperative form mixin that dynamically creates TagMe fields for all tagged models.

    This specialized mixin automatically generates form fields for all TaggedFieldModel
    instances associated with the current user. It's useful for creating comprehensive
    tag management interfaces where users can manage tags across multiple models.

    Key Features:
    - Dynamically creates form fields based on TaggedFieldModel entries
    - Requires authenticated user (raises exception if missing)
    - Integrates with UserTag model for personalized tag management
    - Designed for cooperative inheritance
    - Provides comprehensive error handling and logging

    Usage:
        class TagManagementForm(AllFieldsTagMeModelFormMixin, forms.Form):
            # Fields are dynamically added based on TaggedFieldModel entries
            pass

        # With other mixins
        class ComprehensiveForm(AllFieldsTagMeModelFormMixin, BlockNoteUserFormMixin, forms.Form):
            content = forms.CharField(widget=BlockNoteWidget())
            # TagMe fields added dynamically

    Requirements:
    - Requires authenticated user in kwargs
    - TaggedFieldModel entries must exist in database
    - Corresponding UserTag entries should exist for proper functionality

    Dynamic Field Creation:
    For each TaggedFieldModel entry, creates:
    - CharField with TagMeSelectMultipleWidget
    - Proper field labeling from UserTag.field_verbose_name
    - Widget configuration with user context and tag data

    Error Handling:
    - Raises ObjectDoesNotExist if user is missing
    - Logs missing UserTag entries (non-fatal)
    - Graceful degradation for missing data

    Cooperative Design:
    - Shares user extraction pattern with other mixins
    - Maintains compatibility with standard form mixins
    - Preserves user context for downstream mixins

    Performance Notes:
    - Database queries are performed during form initialization
    - Consider caching TaggedFieldModel queries for high-traffic scenarios
    - Queries are optimized with select_related/prefetch_related where applicable
    """

    fields: dict[str, Union[TagMeCharField, forms.Field]]

    def __init__(self, *args, **kwargs):
        """
        Initialize form with dynamic TagMe fields for all tagged models.

        Creates form fields dynamically based on TaggedFieldModel entries
        and the current user's UserTag configuration. Requires authenticated
        user and performs database queries to build the form.

        Args:
            *args: Variable length argument list for parent form
            **kwargs: Keyword arguments including:
                - user: Required authenticated user object

        Raises:
            ObjectDoesNotExist: If user is None or not provided

        Cooperative Behavior:
        - Checks if user was already extracted by another mixin
        - Extracts user from kwargs if not already available
        - Stores user reference as instance attribute

        User Sharing Strategy:
        - First mixin to run extracts user with pop() and stores it
        - Subsequent mixins check for existing self.user attribute
        - This prevents TypeError from unexpected kwargs in Django forms
        """
        # Check if user was already extracted by another mixin
        if hasattr(self, "user"):
            # Another mixin already extracted the user - use that
            user = self.user
        else:
            # First mixin to run - extract user from kwargs
            user = kwargs.pop("user", None)
            self.user = user

        # Validate user requirement
        if self.user is None:
            msg = "User is required for AllFieldsTagMeModelFormMixin"
            logger.exception(msg)
            raise ObjectDoesNotExist(msg)

        # Initialize parent form
        super().__init__(*args, **kwargs)

        # Create dynamic fields based on tagged models
        self._create_dynamic_tagme_fields()

    def _create_dynamic_tagme_fields(self):
        """
        Create form fields dynamically based on TaggedFieldModel entries.

        Queries the database for TaggedFieldModel entries and creates
        corresponding form fields with TagMeSelectMultipleWidget widgets.
        Each field is configured with user context and existing tag data.

        Database Queries:
        - TaggedFieldModel.objects.all() for available tagged fields
        - UserTag.objects.filter(user=self.user) for user-specific tags

        Field Configuration:
        Each generated field includes:
        - CharField base with TagMeSelectMultipleWidget
        - User context in widget attrs
        - Existing tag data for the user
        - Proper field labeling and metadata

        Error Handling:
        - Logs missing UserTag entries (continues processing)
        - Handles ObjectDoesNotExist exceptions gracefully
        - Provides debugging information for development
        """
        # Query for all tagged models and user tags
        tagged_models = TaggedFieldModel.objects.all()
        user_tags = UserTag.objects.filter(user=self.user)

        created_fields = 0

        # Create fields for each tagged model
        for tagged_model in tagged_models:
            try:
                # Find corresponding user tag
                user_tag = user_tags.get(
                    model_name=tagged_model.model_name,
                    field_name=tagged_model.field_name,
                )

                # Create form field with TagMe widget
                self.fields[user_tag.field_name] = forms.CharField(
                    required=False,
                    label=user_tag.field_verbose_name,
                    widget=TagMeSelectMultipleWidget(
                        attrs={
                            "all_tag_fields_mixin": True,
                            "display_all_tags": False,
                            "user": self.user,
                            "field_name": user_tag.field_name,
                            "all_tag_fields_tag_string": user_tag.tags,
                        },
                    ),
                )
                created_fields += 1

                # Debug logging
                if hasattr(self, "_debug_widget_config"):
                    logger.debug(
                        event="_create_dynamic_tagme_fields",
                        msg=(
                            f"✅ Created dynamic TagMe field '{user_tag.field_name}' "
                            f"for model {tagged_model.model_name}"
                        ),
                    )

            except ObjectDoesNotExist as e:
                # Log missing UserTag but continue processing
                msg = (
                    f"UserTag does not exist for {tagged_model.model_name}:"
                    f"{tagged_model.field_name} - field will be skipped"
                )
                logger.exception(
                    event="_create_dynamic_tagme_fields",
                    msg=msg,
                    data={
                        "error": e,
                    },
                )

        # Optional debug output
        if created_fields > 0 and hasattr(self, "_debug_widget_config"):
            logger.debug(
                event="_create_dynamic_tagme_fields",
                msg=f"🏷️ Created {created_fields} dynamic TagMe field(s)",
            )


# class TagMeModelFormMixin:
#     """
#     Mixin for Django ModelForms that enhances TagMeCharField fields.
#
#     This mixin provides additional configuration and behavior for `TagMeCharField` fields within a ModelForm. It allows for customization based on the current user.
#     """
#
#     fields: dict[str, Union[TagMeCharField, forms.Field]]
#
#     def __init__(self, *args, **kwargs):
#         """
#         Initializes the form, extracting the current user from keyword arguments.
#
#         Args:
#             *args: Variable length argument list passed to the parent ModelForm's __init__.
#             **kwargs: Arbitrary keyword arguments passed to the parent ModelForm's __init__.
#                  - user: (Optional) The current user object.
#         """
#
#         self.user = kwargs.pop("user", None)
#         self.model_obj = kwargs.pop("model_obj", None)
#         self.model_verbose_name = kwargs.pop("model_verbose_name", None)
#         self.model_name = kwargs.pop("model_name", None)
#         super().__init__(*args, **kwargs)  # Call the original form's __init__
#
#         # Process fields
#         for _, field in self.fields.items():
#             if isinstance(field, TagMeCharField):
#                 field.widget.attrs.update(
#                     {
#                         "css_class": "",
#                         "user": self.user,
#                     }
#                 )
#
#
# class AllFieldsTagMeModelFormMixin:
#     """
#     Mixin for Django ModelForms that enhances TagMeCharField fields.
#
#     This mixin provides additional configuration and behavior for `TagMeCharField` fields within a ModelForm. It allows for customization based on the current user.
#     """
#
#     fields: dict[str, Union[TagMeCharField, forms.Field]]
#
#     def __init__(self, *args, **kwargs):
#         """
#         Initializes the form, extracting the current user from keyword arguments.
#
#         Args:
#             *args: Variable length argument list passed to the parent ModelForm's __init__.
#             **kwargs: Arbitrary keyword arguments passed to the parent ModelForm's __init__.
#                  - user: (Optional) The current user object.
#         """
#
#         self.user = kwargs.pop("user", None)
#         if self.user is None:
#             msg = "User is required for AllFieldsTagMeModelFormMixin"
#             logger.exception(msg)
#             raise ObjectDoesNotExist(msg)
#         super().__init__(*args, **kwargs)
#
#         tagged_models = TaggedFieldModel.objects.all()
#         user_tags = UserTag.objects.filter(user=self.user)
#         # Get the user tag to process
#         for tagged_model in tagged_models:
#             try:
#                 user_tag = user_tags.get(
#                     model_name=tagged_model.model_name,
#                     field_name=tagged_model.field_name,
#                 )
#                 self.fields[user_tag.field_name] = forms.CharField(
#                     required=False,
#                     label=user_tag.field_verbose_name,
#                     widget=TagMeSelectMultipleWidget(
#                         attrs={
#                             "all_tag_fields_mixin": True,
#                             "display_all_tags": False,
#                             "user": self.user,
#                             "all_tag_fields_tag_string": user_tag.tags,
#                         },
#                     ),
#                 )
#             except ObjectDoesNotExist:
#                 msg = f"User Tag does not exist {tagged_model.model_name}:{tagged_model.field_name}"
#                 logger.exception(msg)
