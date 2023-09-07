"""tags Models file."""
# import json
# from collections import UserList

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

# from django.core import serializers
from django.db import IntegrityError, models, router, transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify

# from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

User = settings.AUTH_USER_MODEL

try:
    """Ported from django-taggit
    https://github.com/jazzband/django-taggit/tree/master
    """
    from unidecode import unidecode
except ImportError:

    def unidecode(tag):
        return tag


class TaggedFieldModel(models.Model):
    """Store all the details of models with field tags.

    This table is populatd using a management command.
    When a new tagged field is added to a model, run ./manage.py tags -U
    """

    class Meta:
        verbose_name = _("Tagged Field Model")
        verbose_name_plural = _("Tagged Field Models")

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


class TagBase(models.Model):
    """Base class for Tag models.

    PARAMATERS
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
        verbose_name = _("Tag ABC")
        verbose_name_plural = _("Tags ABC")

    name = models.CharField(
        verbose_name=pgettext_lazy("A tag name", "Name"),
        blank=False,
        null=False,
        max_length=50,
    )

    slug = models.SlugField(
        verbose_name=pgettext_lazy("A tag slug", "slug"),
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


class UserTag(TagBase):
    """A user tag for a specific model field.

    Extends Tag base class and enforces Foreign Keys.

    Use this model to create or modify all new User Tags.


    PARAMATERS
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
        verbose_name = _("User Tag")
        verbose_name_plural = _("User Tags")
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
                    "field",
                    "name",
                ],
                name="unique_user_field_tag",
            )
        ]
        ordering = [
            "feature",
            "field",
            "name",
        ]

    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="user_tags",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="user_tag_content_id",
        verbose_name=_("Content ID"),
        default=None,
    )
    feature = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_("Feature"),
        default=None,
    )
    comment = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_("Comment"),
    )
    field = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_("Field"),
    )

    def __str__(self) -> str:
        return f"{self.user.username}:{self.feature}:{self.field}:{self.name}"

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
