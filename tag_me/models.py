"""tags Models file."""

import copy
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, router, transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy as _

User = settings.AUTH_USER_MODEL

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
            "This is the tag",
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
        """Ported from django-taggit
        https://github.com/jazzband/django-taggit/tree/master
        """
        if self._state.adding and not self.slug:
            self.slug = self.slugify(self.tags)
            using = kwargs.get("using") or router.db_for_write(
                type(self), instance=self
            )
            # Make sure we write to the same db for all attempted writes,
            # with a multi-master setup, theoretically we could try to
            # write and rollback on different DBs
            kwargs["using"] = using
            # Be opportunistic and try to save the tag, this should work for
            # most cases ;)
            try:
                with transaction.atomic(using=using):
                    res = super().save(*args, **kwargs)
                return res
            except IntegrityError:
                pass
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

    def _get_field_name_models_to_sync(self, field: str = None) -> bool:
        """"""
        if field in self.synchronise.keys():
            return self.synchronise.get(field)

    def _add_model_to_sync_list(
        self,
        content_type_id: str = None,
        field: str = None,
    ):
        if not content_type_id | field:
            return False
        if content_type_id not in self.synchronise[field]:
            self.synchronise[field].append(content_type_id)
            return True

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
        logger = logging.getLogger(__name__)
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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "content",
                    "model_name",
                    "model_verbose_name",
                    "field_name",
                    "field_verbose_name",
                ],
                name="unique_tagged_field_model",
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

    model_name = models.CharField(
        max_length=128,
        editable=False,
    )
    model_verbose_name = models.CharField(
        max_length=128,
        editable=False,
    )

    field_name = models.CharField(
        max_length=128,
        editable=False,
    )

    field_verbose_name = models.CharField(
        max_length=128,
        editable=False,
    )
    tag_type = models.CharField(
        verbose_name=_(
            "Verbose name",
            "tags",
        ),
        blank=False,
        null=False,
        default="user",
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

    def __str__(self):
        return f"{self.model_verbose_name} - {self.field_verbose_name}"


# A store for synchronised tags, that are yet to be saved
add_synced_user_tags_list = []


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
        related_name="tagged_field",
        on_delete=models.CASCADE,
        verbose_name=_(
            "Verbose name",
            "Tagged Field",
        ),
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

    def __str__(self) -> str:
        return f"{self.id}:{self.user.username}:{self.model_verbose_name}:{self.field_name}:{self.tags}"

    def save(
        self,
        name: str = "default",
        sync_tags_save: bool = False,
        *args,
        **kwargs,
    ):
        """
        Saves the model instance and optionally synchronises related tags.

        This method allows you to control whether related tags from synchronised
        content types will also be updated when the model saves.
        :param name: The name of the syncronisation key to use.
                                Defaults to default
        :param sync_tags_save: If True, tags on related content types configured
                               for synchronisation will be updated.  Defaults to False.
        :param args: Additional positional arguments passed to the superclass's save method.
        :param kwargs: Additional keyword arguments passed to the superclass's save method.

        """
        # We don't need to gather synchronising information if the save is
        # for synchronising tags.  The information has already been collected
        if not sync_tags_save:
            sync, _ = TagMeSynchronise.objects.get_or_create(
                name=name,
            )
            # Check if tags should be synced for a specific field
            if self.field_name in sync.synchronise.keys():
                # Get other objects with this tag ( then exclude the current one)
                content_ids = copy.deepcopy(
                    sync.synchronise[self.field_name],
                )
                content_ids.remove(
                    self.tagged_field.content_id,
                )

                for content_id in content_ids:
                    tagged_field_model = TaggedFieldModel.objects.get(
                        content=content_id,
                        model_name=ContentType.objects.get(id=content_id)
                        .model_class()
                        .__name__,
                        field_name=self.field_name,
                    )

                    instance = UserTag.objects.get(
                        user=self.user,
                        tagged_field=tagged_field_model,
                    )

                    instance.tags = self.tags
                    instance.save(
                        sync_tags_save=True,
                    )

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
