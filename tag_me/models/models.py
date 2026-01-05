"""tags Models file."""

import copy
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, router, transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy as _

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL

# Valid tag types - extend this list if new tag types are added
TAG_TYPES = ["user", "system"]
TAG_TYPE_DEFAULT = "user"

try:
    """Ported from django-taggit
    https://github.com/jazzband/django-taggit/tree/master
    """
    from unidecode import unidecode
except ImportError:

    def unidecode(tag):
        return tag


class TagBase(models.Model):
    """Base class for Tag models.

    PARAMETERS
    ----------

    :param name: Text max 255 characters

            Required

            The tag name that will be used in the model field.

    :param slug: Text max 255 characters

            Optional

            If not supplied this will be generated automatically.

            Automatic generation ensures the slug is unique.

    """

    class Meta:
        abstract = True
        verbose_name = _(
            "Verbose name",
            "Tag ABC",
        )
        verbose_name_plural = _(
            "Verbose name",
            "Tags ABC",
        )

    search_tags = models.TextField(
        verbose_name=_(
            "Verbose name",
            "Search Tags",
        ),
        default="",
        blank=True,
        help_text=_(
            "Help",
            "A list of every tag created, for use in search tools",
        ),
    )

    tags = models.CharField(
        verbose_name=_(
            "Verbose name",
            "tags",
        ),
        default="",
        blank=True,
        null=True,
        max_length=255,
        help_text=_(
            "Help",
            "The tags that are considered active and in use by the user",
        ),
    )

    slug = models.SlugField(
        verbose_name=_(
            "Verbose name",
            "slug",
        ),
        editable=False,
        unique=True,
        max_length=100,
        allow_unicode=True,
    )

    @property
    def model_class_name(self):
        return self.__class__.__name__

    @property
    def model_class_verbose_name(self):
        return self._meta.verbose_name

    def save(self, *args, **kwargs):
        """Base save method that handles slug generation and search_tags merging"""

        # Update search_tags by merging current tags with historical tags
        if self.tags:
            tags_to_process = self.tags.rstrip(",")
            search_tags_to_process = (self.search_tags or "").rstrip(",")

            current_tags = set(
                tag.strip() for tag in tags_to_process.split(",") if tag.strip()
            )
            existing_tags = set(
                tag.strip() for tag in search_tags_to_process.split(",") if tag.strip()
            )

            search_tags_set = existing_tags.union(current_tags)
            self.search_tags = ",".join(sorted(search_tags_set)) + ","

        # Slug generation with retry logic for collisions
        if self._state.adding and not self.slug:
            using = kwargs.get("using") or router.db_for_write(
                type(self), instance=self
            )
            kwargs["using"] = using

            # Retry up to 5 times if slug collision occurs
            max_retries = 5
            for attempt in range(max_retries):
                self.slug = self.slugify(self.tags)
                try:
                    with transaction.atomic(using=using):
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    if attempt == max_retries - 1:
                        # Give up after max retries - re-raise the exception
                        logger.error(
                            f"Failed to generate unique slug after {max_retries} attempts "
                            f"for {self.__class__.__name__}"
                        )
                        raise
                    # Otherwise, continue to retry with a new slug
                    continue
        else:
            return super().save(*args, **kwargs)

    @staticmethod
    def slugify(tag: str = "") -> str:
        if getattr(settings, "TAGS_STRIP_UNICODE_WHEN_SLUGIFYING", False):
            slug = slugify(
                unidecode(tag)
                + "-"
                + get_random_string(8, f"abcdqrwxyz{tag}0123456789")
            )
        else:
            slug = slugify(
                tag + "-" + get_random_string(8, f"abcdqrwxyz{tag}0123456789"),
                allow_unicode=True,
            )

        return slug


class TagMeSynchronise(models.Model):
    """
    Internal model for managing tag synchronization configuration.

    This model maintains an internal registry of models and their fields
    configured with attribute `synchronise=True` indicating that tags applied
    to those fields should be synchronised across related content types.
    This configuration is used by the 'tag-me' library.

    Do not interact with this model directly. When tagged fields are added,
    modified, or have the 'synchronise' attribute changed you must update
    the registry.
    To update the registry after adding or modifying tagged fields,
    use the management command:  ./manage.py tags -U
    """

    class Meta:
        verbose_name = _(
            "Verbose name",
            "Tags Synchronised",
        )
        verbose_name_plural = _(
            "Verbose name",
            "Tags Synchronised",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                ],
                name="unique_tag_synchronise_name",
            )
        ]

    name = models.CharField(
        max_length=255,
        default="default",
    )
    synchronise = models.JSONField(
        blank=True,
        null=True,
        default=dict,
    )

    def _get_field_name_models_to_sync(self, field: str = None) -> list | None:
        """Get the list of content type IDs that should sync for a given field.

        Args:
            field: The field name to look up.

        Returns:
            List of content type IDs, or None if field not in sync config.
        """
        return self.synchronise.get(field)

    def _add_model_to_sync_list(
        self,
        content_type_id: str = None,
        field: str = None,
    ):
        """Add a content type to the sync list for a field.

        Returns True if added, False if already present or invalid input.
        """
        if content_type_id is None or field is None:
            return False
        if field not in self.synchronise:
            self.synchronise[field] = []
        if content_type_id not in self.synchronise[field]:
            self.synchronise[field].append(content_type_id)
            return True
        return False  # Already in list

    def check_field_sync_list_lengths(self):
        """
        Performs a sanity check on field synchronization configurations.

        This method examines the lengths of synchronization lists (stored in
        the 'synchronise' attribute) and logs warnings or informational
        messages to help developers identify potential issues:

        * **Lists with zero entries:** Warns about fields that might need
        removal from the synchronization configuration.
        * **Lists with one entry:** Warns about potentially incomplete
            configurations.
        * **Lists with two or more entries:** Provides information depending
            on the length, considering a two-item synchronization list as the
            expected minimum.
        """
        if self.synchronise.items():
            for k, v in self.synchronise.items():
                match len(v):
                    case 0:
                        logger.warning(
                            "Field <%s> has no content id's listed that require synchronising.\nPlease consider removing this key from the sync list.",
                            k,
                        )
                    case 1:
                        logger.warning(
                            "Field <%s> only has 1 element, content id is %s\nHave you forgotten to add synchronise=True to another model <%s> field?",
                            k,
                            v,
                            k,
                        )
                    case 2:
                        logger.info(
                            "Your field <%s> sync list has 2 required minumum elements with content id's %s ",
                            k,
                            v,
                        )
                    case _:
                        logger.info(
                            "Your field <%s> sync list has more than the 2 required minumum elements with content id's %s ",
                            k,
                            v,
                        )

        else:
            logger.info("You have no field tags listed that require synchronising")


class TaggedFieldModel(models.Model):
    """
    Stores configuration details for fields using the 'tag-me' library.

    This model maintains an internal registry of models and their fields
    configured for tagging.
    Do not interact with this model directly. To update the registry after
    adding or modifying tagged fields, use the management
    command:  ./manage.py tags -U

    IMPORTANT: Lookups should use `content` (ContentType FK) + `field_name`,
    NOT `model_name`. The `model_name` field is cached for display purposes
    only and may become stale if models are renamed.
    """

    class Meta:
        verbose_name = _(
            "Verbose name",
            "Tagged Field Model",
        )
        verbose_name_plural = _(
            "Verbose name",
            "Tagged Field Models",
        )
        # CHANGED: Simplified constraint - uses ContentType FK as identifier
        # This ensures model renames don't break lookups
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "content",
                    "field_name",
                ],
                name="unique_tagged_field_content_field",
            ),
        ]

        ordering = [
            "model_name",
            "field_name",
            "tag_type",
        ]

    content = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        editable=False,
    )

    # NOTE: model_name is kept for display/caching purposes only.
    # Always use `content` FK for lookups to survive model renames.
    model_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        editable=False,
        verbose_name=_(
            "Verbose name",
            "Model name",
        ),
        help_text="Cached model name for display. Use content FK for lookups.",
    )
    model_verbose_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        editable=False,
        verbose_name=_(
            "Verbose name",
            "Model verbose name",
        ),
    )

    field_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        editable=False,
        verbose_name=_(
            "Verbose name",
            "Field name",
        ),
    )

    field_verbose_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        editable=False,
        verbose_name=_(
            "Verbose name",
            "Field verbose name",
        ),
    )
    tag_type = models.CharField(
        verbose_name=_(
            "Verbose name",
            "Tag type",
        ),
        blank=False,
        null=False,
        default=TAG_TYPE_DEFAULT,
        max_length=20,
        editable=False,
        help_text=_(
            "Help",
            "This is the tag type, default is 'user'.",
        ),
    )
    default_tags = models.CharField(
        verbose_name=_(
            "Verbose name",
            "Default tags for field.",
        ),
        blank=True,
        null=True,
        max_length=255,
        help_text=_(
            "Help",
            "These are generated for each new user to get them started.",
        ),
    )

    @property
    def current_model_name(self):
        """
        Get the current model name from ContentType.

        Use this for display when you need the live/current name.
        The stored `model_name` field may be stale after renames.
        """
        return self.content.model

    @property
    def current_model_class(self):
        """
        Get the actual model class from ContentType.

        Returns None if the model no longer exists (e.g., was deleted).
        """
        return self.content.model_class()

    @property
    def app_label(self):
        """Get the app label from ContentType."""
        return self.content.app_label

    def save(self, *args, **kwargs):
        """
        Save with validation to ensure required fields are present.

        While the database columns are nullable for migration flexibility,
        we enforce that field_name must be present at the application level.
        A TaggedFieldModel without a field_name is semantically meaningless.
        """
        if not self.field_name:
            raise ValueError(
                "TaggedFieldModel.field_name cannot be empty. "
                "Every TaggedFieldModel must reference a specific field."
            )
        if not self.content_id:
            raise ValueError(
                "TaggedFieldModel.content cannot be empty. "
                "Every TaggedFieldModel must reference a ContentType."
            )
        if self.tag_type not in TAG_TYPES:
            raise ValueError(
                f"TaggedFieldModel.tag_type must be one of {TAG_TYPES}, "
                f"got '{self.tag_type}'."
            )
        super().save(*args, **kwargs)

    def __str__(self):
        model = self.model_verbose_name or self.model_name or "Unknown Model"
        field = self.field_verbose_name or self.field_name or "Unknown Field"
        return f"{model} - {field}"


class UserTag(TagBase):
    """A user tag for a specific model field.

    Extends Tag base class and enforces Foreign Keys.

    Use this model to create or modify all new User Tags.


    PARAMETERS
    ----------

    :param user: fk - settings.AUTH_USER_MODEL  (CustomUser)

            Required

    :param content_type_id: fk - ContentType

            Required

            content_type can be supplied using.

            ContentType.objects.get_for_model(my-model-instance, for_concrete_model=True) # noqa: E501

    :param content_model: ContentType model

            Required

            content_model can be supplied using.

            ContentType.objects.get_for_model(my-model-instance, for_concrete_model=True).model

    :param comment: Text max 255 characters

            Optional

    :param field: Text max 255 characters

            Required

            Must be a valid model field name.



    """

    # objects = UserTagsManager()

    class Meta:
        verbose_name = _(
            "Verbose name",
            "User Tag",
        )
        verbose_name_plural = _(
            "Verbose name",
            "User Tags",
        )
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "tagged_field",
                    "tags",
                ]
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "tagged_field",
                ],
                name="unique_user_field_tag",
            )
        ]
        ordering = [
            "model_verbose_name",
            "field_name",
            "tags",
        ]

    objects = models.Manager()
    tagged_field = models.ForeignKey(
        TaggedFieldModel,
        blank=True,
        null=True,
        editable=False,
        related_name="user_tags",
        on_delete=models.CASCADE,
        verbose_name=_(
            "Verbose name",
            "Tagged Field",
        ),
        help_text="FK to TaggedFieldModel. Use this for lookups instead of model_name.",
    )

    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        editable=False,
        related_name="user_tags",
        on_delete=models.CASCADE,
        verbose_name=_(
            "Verbose name",
            "User",
        ),
    )
    model_verbose_name = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        editable=False,
        verbose_name=_(
            "Verbose name",
            "Model verbose",
        ),
        default=None,
    )

    # NOTE: model_name is kept for display/caching purposes only.
    # Always use `tagged_field` FK for lookups to survive model renames.
    model_name = models.CharField(
        blank=True,
        null=True,
        editable=False,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Model name",
        ),
        default=None,
        help_text="Cached model name for display. Use tagged_field FK for lookups.",
    )

    comment = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Comment",
        ),
    )

    field_name = models.CharField(
        blank=True,
        null=True,
        editable=False,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field name",
        ),
    )

    field_verbose_name = models.CharField(
        blank=True,
        null=True,
        editable=False,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field verbose",
        ),
        default=None,
    )
    ui_display_name = models.CharField(
        verbose_name=_(
            "Verbose name",
            "UI Display Name",
        ),
        blank=True,
        null=True,
        max_length=50,
        help_text=_(
            "Help",
            "This is the user customisable ui display name.",
        ),
    )

    meta = models.JSONField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field meta data",
        ),
        default=dict,
    )

    @property
    def current_model_name(self):
        """
        Get the current model name from the related TaggedFieldModel's ContentType.

        Use this for display when you need the live/current name.
        """
        if self.tagged_field:
            return self.tagged_field.current_model_name
        return self.model_name  # Fallback to cached value

    def __str__(self) -> str:
        username = self.user.username if self.user else "NO_USER"
        return f"{self.id}:{username}:{self.model_verbose_name}:{self.field_name}:{self.tags}"

    def save(
        self,
        name: str = "default",
        sync_tags_save: bool = False,
        *args,
        **kwargs,
    ):
        """Saves with optional tag synchronization"""

        # Handle synchronization if needed
        if not sync_tags_save:
            sync, _ = TagMeSynchronise.objects.get_or_create(name=name)

            if self.field_name in sync.synchronise.keys():
                # Skip synchronization if tagged_field is not set (orphaned record)
                if self.tagged_field is None:
                    logger.warning(
                        f"UserTag {self.id} has no tagged_field FK - "
                        f"skipping tag synchronization for field '{self.field_name}'"
                    )
                else:
                    content_ids = copy.deepcopy(sync.synchronise[self.field_name])

                    # Safely remove current content_id if present
                    if self.tagged_field.content_id in content_ids:
                        content_ids.remove(self.tagged_field.content_id)

                    for content_id in content_ids:
                        # CHANGED: Use content_id only, not model_name
                        # This ensures lookups work even if model was renamed
                        try:
                            tagged_field_model = TaggedFieldModel.objects.get(
                                content_id=content_id,
                                field_name=self.field_name,
                            )
                            instance = UserTag.objects.get(
                                user=self.user,
                                tagged_field=tagged_field_model,
                            )
                            instance.tags = self.tags
                            instance.save(sync_tags_save=True)
                        except (
                            TaggedFieldModel.DoesNotExist,
                            UserTag.DoesNotExist,
                        ) as e:
                            logger.warning(
                                f"Could not sync tags for content_id={content_id}, "
                                f"field_name={self.field_name}: {e}"
                            )

        # Call parent save (which handles search_tags merging)
        super().save(*args, **kwargs)


class SystemTag(TagBase):
    """System Tag"""

    class Meta:
        verbose_name = _(
            "Verbose name",
            "System Tag",
        )
        verbose_name_plural = _(
            "Verbose name",
            "System Tags",
        )
        constraints = [
            # Ensure only one SystemTag per TaggedFieldModel
            # Conditional to handle legacy NULL values (NULL != NULL in SQL)
            models.UniqueConstraint(
                fields=["tagged_field"],
                name="unique_system_tag_field",
                condition=models.Q(tagged_field__isnull=False),
            )
        ]

    tagged_field = models.ForeignKey(
        TaggedFieldModel,
        blank=True,
        null=True,
        editable=False,
        related_name="system_tags",
        on_delete=models.CASCADE,
        verbose_name=_(
            "Verbose name",
            "Tagged Field",
        ),
        help_text="FK to TaggedFieldModel. Use this for lookups instead of model_name.",
    )

    model_verbose_name = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        editable=False,
        verbose_name=_(
            "Verbose name",
            "Model verbose",
        ),
        default=None,
    )

    model_name = models.CharField(
        blank=True,
        null=True,
        editable=False,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Model name",
        ),
        default=None,
        help_text="Cached model name for display. Use tagged_field FK for lookups.",
    )

    comment = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Comment",
        ),
    )

    field_name = models.CharField(
        blank=True,
        null=True,
        editable=False,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field name",
        ),
    )

    field_verbose_name = models.CharField(
        blank=True,
        null=True,
        editable=False,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field verbose",
        ),
        default=None,
    )

    ui_display_name = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        help_text="Display name for the tag in UI",
    )

    meta = models.JSONField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field meta data",
        ),
        default=dict,
    )

    @property
    def current_model_name(self):
        """
        Get the current model name from the related TaggedFieldModel's ContentType.
        """
        if self.tagged_field:
            return self.tagged_field.current_model_name
        return self.model_name

    def __str__(self) -> str:
        model = self.model_verbose_name or self.model_name or "Unknown Model"
        field = self.field_verbose_name or self.field_name or "Unknown Field"
        return f"{self.id}:{model}:{field}:{self.tags}"
