"""tag-me app custom form widget."""

import json
import logging
from typing import Callable, Optional, Union

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.urls import reverse
from django.utils.safestring import mark_safe

from tag_me.assets import (
    get_tag_me_css,
    get_tag_me_js,
)
from tag_me.models import SystemTag, UserTag

User = get_user_model()
logger = logging.getLogger(__name__)

# Type alias for choices parameter
ChoicesType = Union[list[str], str, Callable[[], list[str]], None]


class TagMeSelectMultipleWidget(forms.SelectMultiple):
    """
    A multi-select widget for tag selection with Alpine.js frontend.

    Can be used in two modes:

    1. **Database-driven** (default, via model field):
       Automatically queries UserTag/SystemTag based on ``tagged_field`` and ``user``
       passed through attrs. This is the standard usage with TagMeCharField model fields.

    2. **Standalone** (explicit configuration):
       Provide choices and configuration directly via constructor parameters.
       Useful for forms without model backing or custom tag sources.

    Examples::

        # Standalone usage - static choices
        class MyForm(forms.Form):
            tags = TagMeCharField(
                widget=TagMeSelectMultipleWidget(
                    choices=['Python', 'Django', 'JavaScript'],
                    multiple=True,
                    permitted_to_add_tags=False,
                )
            )

        # Standalone usage - dynamic choices per user
        class MyForm(forms.Form):
            tags = TagMeCharField()

            def __init__(self, *args, user=None, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['tags'].widget = TagMeSelectMultipleWidget(
                    choices=get_choices_for_user(user),
                    permitted_to_add_tags=False,
                )

        # Database-driven (existing pattern via model field)
        # Configured automatically through TagMeCharField.formfield()

    Args:
        choices: Tag choices as list of strings, CSV string, or callable.
            If None, falls back to database query via attrs.
        multiple: Allow multiple tag selection. Default True.
        permitted_to_add_tags: Allow users to create new tags. Default True.
            If True without add_tag_url, adding is disabled automatically.
        auto_select_new_tags: Auto-select newly created tags. Default True.
        display_number_selected: Max tags to display before "+N more".
            Falls back to settings.DJ_TAG_ME_MAX_NUMBER_DISPLAYED.
        add_tag_url: URL endpoint for creating new tags.
            Required if permitted_to_add_tags=True in standalone mode.
        help_url: URL for help documentation. Falls back to settings.
        mgmt_url: URL for tag management. Falls back to settings.
        template: Template path for rendering. Falls back to settings.
        tag_type: "user" or "system". Affects behavior when using DB queries.
            Default "user".
        attrs: Additional HTML attributes (existing Django widget pattern).

    Note:
        For dynamic choices that vary per-user or per-request, always instantiate
        the widget in the form's ``__init__`` method, not at class level.
    """

    multiple = True

    class Media:
        """Widget media files using Vite manifest for hashed filenames."""

        css = {"all": (get_tag_me_css(),)}
        js = (get_tag_me_js(),)

    def __init__(
        self,
        choices: ChoicesType = None,
        multiple: Optional[bool] = None,
        permitted_to_add_tags: Optional[bool] = None,
        auto_select_new_tags: Optional[bool] = None,
        display_number_selected: Optional[int] = None,
        add_tag_url: Optional[str] = None,
        help_url: Optional[str] = None,
        mgmt_url: Optional[str] = None,
        template: Optional[str] = None,
        tag_type: Optional[str] = None,
        attrs: Optional[dict] = None,
    ):
        """
        Initialize the widget.

        All parameters are optional. When not provided, values are resolved
        using the priority chain: explicit parameter > attrs > settings > default.

        This ensures backwards compatibility with existing database-driven usage
        while enabling standalone usage with explicit configuration.

        Standalone Mode:
            When ``choices`` is provided explicitly, the widget operates in
            standalone mode. In this mode:

            - ``permitted_to_add_tags`` is forced to False (no backend to save to)
            - ``add_tag_url`` is ignored (no endpoint exists)
            - ``mgmt_url`` is ignored (no tag management available)
            - ``help_url`` is still allowed (documentation link)

            This ensures the widget behaves safely without a database backend.
        """
        super().__init__(attrs=attrs)

        # Store explicit parameters (None means "not set, check attrs/defaults")
        self._explicit_choices = choices
        self._explicit_multiple = multiple
        self._explicit_permitted_to_add_tags = permitted_to_add_tags
        self._explicit_auto_select_new_tags = auto_select_new_tags
        self._explicit_display_number_selected = display_number_selected
        self._explicit_add_tag_url = add_tag_url
        self._explicit_help_url = help_url
        self._explicit_mgmt_url = mgmt_url
        self._explicit_template = template
        self._explicit_tag_type = tag_type

    @property
    def _is_standalone(self) -> bool:
        """
        Check if widget is in standalone mode.

        Standalone mode is active when choices are provided explicitly,
        meaning no database queries are needed for tag options.

        Returns:
            bool: True if choices were provided explicitly.
        """
        return self._explicit_choices is not None

    def _resolve_config(self) -> dict:
        """
        Resolve configuration using priority chain: explicit > attrs > defaults.

        In standalone mode (choices provided explicitly), certain settings are
        forced to ensure safe operation without a database backend:

        - ``permitted_to_add_tags``: Forced False
        - ``add_tag_url``: Forced empty
        - ``mgmt_url``: Forced empty
        - ``help_url``: Still configurable

        Returns:
            dict: All resolved configuration values.
        """

        def resolve(explicit, attr_key, default):
            """Helper to resolve value with fallback chain."""
            if explicit is not None:
                return explicit
            if attr_key and self.attrs.get(attr_key) is not None:
                return self.attrs.get(attr_key)
            return default

        is_standalone = self._is_standalone

        return {
            "multiple": resolve(self._explicit_multiple, "multiple", True),
            # Standalone: forced False (no backend to save new tags)
            "permitted_to_add_tags": False
            if is_standalone
            else resolve(self._explicit_permitted_to_add_tags, None, True),
            "auto_select_new_tags": resolve(
                self._explicit_auto_select_new_tags, "auto_select_new_tags", True
            ),
            "display_number_selected": resolve(
                self._explicit_display_number_selected,
                "display_number_selected",
                getattr(settings, "DJ_TAG_ME_MAX_NUMBER_DISPLAYED", 2),
            ),
            # Standalone: forced empty (no endpoint exists)
            "add_tag_url": ""
            if is_standalone
            else resolve(self._explicit_add_tag_url, None, ""),
            # Standalone: help URL still allowed
            "help_url": resolve(
                self._explicit_help_url,
                None,
                getattr(settings, "DJ_TAG_ME_URLS", {}).get("help_url", ""),
            ),
            # Standalone: forced empty (no tag management available)
            "mgmt_url": ""
            if is_standalone
            else resolve(
                self._explicit_mgmt_url,
                None,
                getattr(settings, "DJ_TAG_ME_URLS", {}).get("mgmt_url", ""),
            ),
            "template": resolve(
                self._explicit_template,
                "template",
                getattr(settings, "DJ_TAG_ME_TEMPLATES", {}).get(
                    "default", "tag_me/tag_me_select.html"
                ),
            ),
            "tag_type": resolve(self._explicit_tag_type, "tag_type", "user"),
        }

    def _resolve_choices(self, config: dict) -> tuple[list[str], str]:
        """
        Resolve tag choices from explicit value, callable, or database.

        Priority:
            1. Explicit choices (list, string, or callable)
            2. Database query via tagged_field + user (existing behavior)
            3. Empty list

        Args:
            config: Resolved configuration dict.

        Returns:
            tuple: (choices_list, add_tag_url)
                - choices_list: List of tag strings (with empty string at start)
                - add_tag_url: URL for adding tags (may be updated from DB query)
        """
        add_tag_url = config["add_tag_url"]

        # Priority 1: Explicit choices (standalone mode)
        if self._explicit_choices is not None:
            choices = self._explicit_choices

            # Handle callable - invoke at render time
            if callable(choices):
                try:
                    choices = choices()
                except Exception as e:
                    logger.exception(f"Error calling choices callable: {e}")
                    return [""], add_tag_url

            # Handle CSV string
            if isinstance(choices, str):
                choices = [tag.strip() for tag in choices.split(",") if tag.strip()]

            # Ensure list of strings with empty first option
            if isinstance(choices, (list, tuple)):
                return [""] + list(choices), add_tag_url

            logger.warning(f"Unexpected choices type: {type(choices)}")
            return [""], add_tag_url

        # Priority 2: Database query (existing DB-driven behavior)
        return self._resolve_choices_from_db(config)

    def _resolve_choices_from_db(self, config: dict) -> tuple[list[str], str]:
        """
        Query database for choices (existing behavior for model field usage).

        This method maintains backwards compatibility with the database-driven
        pattern used by TagMeCharField model fields.

        Args:
            config: Resolved configuration dict.

        Returns:
            tuple: (choices_list, add_tag_url)
        """
        add_tag_url = config["add_tag_url"]
        tag_type = config["tag_type"]
        tagged_field = self.attrs.get("tagged_field")
        user = self.attrs.get("user")

        if not tagged_field:
            return [""], add_tag_url

        try:
            if tag_type == "system":
                system_tag = SystemTag.objects.filter(tagged_field=tagged_field).first()

                if system_tag and system_tag.tags:
                    tags_string = system_tag.tags
                    choices = [""] + [
                        tag.strip() for tag in tags_string.split(",") if tag.strip()
                    ]
                    return choices, ""  # No add URL for system tags

            elif tag_type == "user":
                if user and tagged_field:
                    user_tag = UserTag.objects.filter(
                        user=user,
                        tagged_field=tagged_field,
                    ).first()

                    if user_tag:
                        # Generate add URL from UserTag if not explicitly set
                        if not add_tag_url:
                            add_tag_url = reverse("tag_me:add-tag", args=[user_tag.id])

                        if user_tag.tags:
                            tags_string = user_tag.tags
                            choices = [""] + [
                                tag.strip()
                                for tag in tags_string.split(",")
                                if tag.strip()
                            ]
                            return choices, add_tag_url

        except (AttributeError, UserTag.DoesNotExist, SystemTag.DoesNotExist):
            logger.exception("Error retrieving tags from database")

        return [""], add_tag_url

    def _parse_value(self, value) -> list[str]:
        """
        Parse the current field value into a list of selected tags.

        Args:
            value: The field value (string, list, or None).

        Returns:
            list: Selected tag strings.
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [val.strip() for val in value.rstrip(",").split(",") if val.strip()]
        if isinstance(value, (list, tuple)):
            return [str(v).strip() for v in value if str(v).strip()]
        return []

    def render(self, name, value, attrs=None, renderer=None) -> str:
        """
        Render the tag selection widget.

        Args:
            name: The name attribute for the form field.
            value: The currently selected value(s).
            attrs: Additional attributes (merged with widget attrs).
            renderer: Optional custom renderer.

        Returns:
            str: Safe HTML string for the rendered widget.
        """
        # Note: We don't call super().render() because we use a fully custom
        # template that handles string-based choices directly, bypassing
        # Django's optgroups() which expects (value, label) tuples.
        # self.choices = []
        # super().render(name, value, attrs, renderer)

        # Resolve all configuration
        config = self._resolve_config()

        # Resolve choices (explicit or from DB)
        choices, add_tag_url = self._resolve_choices(config)
        self.choices = choices

        # Determine if adding tags is permitted
        permitted_to_add_tags = config["permitted_to_add_tags"]

        # System tags are never user-editable
        if config["tag_type"] == "system":
            permitted_to_add_tags = False

        # Disable adding if no URL available (standalone without endpoint)
        if permitted_to_add_tags and not add_tag_url:
            logger.debug(
                f"Widget '{name}': permitted_to_add_tags=True but no add_tag_url "
                "provided. Tag creation will be disabled."
            )
            permitted_to_add_tags = False

        # Parse current value into list
        values = self._parse_value(value)

        # Get verbose name from attrs if available
        field_verbose_name = self.attrs.get("field_verbose_name", "")

        # Load template
        template = get_template(config["template"])

        # Build context for Alpine.js component
        context = {
            "add_tag_url": add_tag_url,
            "auto_select_new_tags": json.dumps(config["auto_select_new_tags"]),
            "choices": self.choices,
            "display_number_selected": config["display_number_selected"],
            "help_url": config["help_url"],
            "mgmt_url": config["mgmt_url"],
            "multiple": json.dumps(config["multiple"]),
            "name": name,
            "permitted_to_add_tags": json.dumps(permitted_to_add_tags),
            "values": values,
            "verbose_name": field_verbose_name,
        }

        return mark_safe(template.render(context))
