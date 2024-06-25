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

    name = models.CharField(
        verbose_name=_(
            "Verbose name",
            "Name",
        ),
        blank=False,
        null=False,
        max_length=50,
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
        unique=True,
        max_length=100,
        allow_unicode=True,
    )

    def save(self, *args, **kwargs):
        """Ported from django-taggit
        https://github.com/jazzband/django-taggit/tree/master
        """
        if self._state.adding and not self.slug:
            self.slug = self.slugify(self.name)
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

    def slugify(self, tag: str = None) -> str:
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
            logger.info(
                "You have no field tags listed that require synchronising"
            )


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

    content = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    model_name = models.CharField(
        max_length=128,
    )
    model_verbose_name = models.CharField(
        max_length=128,
    )

    field_name = models.CharField(
        max_length=128,
    )

    field_verbose_name = models.CharField(
        max_length=128,
    )

    def __str__(self):
        return f"{self.model_verbose_name}"


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
                    "content_type_id",
                ]
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "content_type_id",
                    "field_name",
                    "name",
                ],
                name="unique_user_field_tag",
            )
        ]
        ordering = [
            "model_verbose_name",
            "field_name",
            "name",
        ]

    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="user_tags",
        on_delete=models.CASCADE,
        verbose_name=_(
            "Verbose name",
            "User",
        ),
    )
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="user_tag_content_id",
        verbose_name=_(
            "Verbose name",
            "Content ID",
        ),
        default=None,
    )
    model_verbose_name = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Feature",
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
        max_length=255,
        verbose_name=_(
            "Verbose name",
            "Field",
        ),
    )

    def __str__(self) -> str:
        return f"{self.user.username}:{self.model_verbose_name}:{self.field_name}:{self.name}"

    def save(self, sync_tags_save: bool = False, *args, **kwargs):
        """
        Saves the model instance and optionally synchronises related tags.

        This method allows you to control whether related tags from synchronised
        content types will also be updated when the model saves.

        :param sync_tags_save: If True, tags on related content types configured
                               for synchronisation will be updated.  Defaults to False.
        :param args: Additional positional arguments passed to the superclass's save method.
        :param kwargs: Additional keyword arguments passed to the superclass's save method.

        """
        # We don't need to gather synchronising information if the save is
        # for synchronising tags.  The information has already been collected
        if not sync_tags_save:
            sync = TagMeSynchronise.objects.get(name="default")
            # Check if tags should be synced for a specific field
            if self.field_name in sync.synchronise.keys():
                # Get other objects with this tag (excluding the current one)
                content_ids = copy.deepcopy(sync.synchronise[self.field_name])
                content_ids.remove(self.content_type_id)
                tagged_models = TaggedFieldModel.objects.filter(
                    content_id__in=content_ids
                ).distinct()
                for content_id in content_ids:
                    syncing_model = ContentType.objects.get(id=content_id)
                    add_synced_user_tags_list.append(
                        UserTag(
                            user=self.user,
                            content_type=syncing_model,
                            model_verbose_name=tagged_models.filter(
                                content_id=content_id
                            )[0].model_verbose_name,
                            comment="Tag created with automatic tag synchronising.",  # noqa: E501
                            field_name=self.field_name,
                            name=self.name,
                            slug=self.slug + "-" + str(content_id),
                        )
                    )

        super().save(*args, **kwargs)

        if add_synced_user_tags_list:
            # Bulk create the new synchronized tags
            for tag in add_synced_user_tags_list:
                add_synced_user_tags_list.remove(tag)
                tag.save(sync_tags_save=True)
        return

    def nothing_here():
        """acc._meta.__dict__["concrete_model"]
                        ContentType.objects.get_for_model(model, for_concrete_model=True) # noqa: E501
                        from django.contrib.contenttypes.models import ContentType # noqa: E501
                        https://docs.djangoproject.com/en/4.1/ref/contrib/contenttypes/#methods-on-contenttype-instances # noqa: E501
                        https://stackoverflow.com/questions/20895429/how-exactly-do-django-content-types-work # noqa: E501
                        https://levelup.gitconnected.com/just-one-index-in-django-makes-your-app-15x-faster-742e2f13108e # noqa: E501
                        'last_login' in [n.name for n in user._meta.fields]
                        https://stackoverflow.com/questions/8702772/django-get-list-of-models-in-application # noqa: E501

        user1=CustomUser.objects.first()
        user2=CustomUser.objects.last()
        pid=Trading.objects.first()
        content=ContentType.objects.get_for_model(pid,for_concrete_model=True)
        tag=UserTag(user=user1,content_type_id=content,content_model=content.model,name="First Tag",field='field-1') # noqa: E501
        tag.save()
        UserTag.objects.create(user=user1,content_type_id=content,content_model=content.model,name="First Tag",field='field-1') # noqa: E501
                    UserTag.objects.create(user=user2,content_type_id=content,content_model=content.model,name="First Tag",field='field-1') # noqa: E501
                    UserTag.objects.create(user=user1,name="First Tag",field='field-1') # noqa: E501
                    https://stackoverflow.com/questions/59600494/what-is-pgettext-lazy-in-django # noqa: E501

        >>> from django.contrib.contenttypes.models import ContentType
        >>> ContentType.objects.filter(app_label="auth")
        <QuerySet [<ContentType: group>, <ContentType: permission>, <ContentType: user>]> # noqa: E501
        >>> [ct.model_class() for ct in ContentType.objects.filter(app_label="auth")] # noqa: E501
        [<class 'django.contrib.auth.models.Group'>, <class 'django.contrib.auth.models.Permission'>, <class 'django.contrib.auth.models.User'>] # noqa: E501



        """
