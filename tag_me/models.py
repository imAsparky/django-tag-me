"""tags Models file."""
# import json
# from collections import UserList

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

# from django.core import serializers
from django.db import models  # router

# from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class TaggedFieldModel(models.Model):
    """Store all the details of models with field tags."""

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


class UserTag(models.Model):
    """A tag for a specific user model field.

    Extends django-tag-fields Tagbase and enforces Foreign Keys.

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

    :param name: Text max 255 characters

            Required

            The tag name that will be used in the model field.

    :param slug: Text max 255 characters

            Optional

            If not supplied this will be generated automatically.

            Automatic generation ensures the slug is unique.

    """

    # objects = UserTagsManager()

    class Meta:
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
    name = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_("Name"),
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
