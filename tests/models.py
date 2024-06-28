"""tests Models file."""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import pgettext_lazy as _

from tag_me.db.models.fields import TagMeCharField
from tag_me.models import TagBase

User = get_user_model()


class TagTestBase(TagBase):
    """A minimal tag to test `TagBase ABC`."""


class TaggedFieldTestModel(TagTestBase):
    """A model for testing the Tag base class"""

    class Meta:
        verbose_name = _(
            "A verbose name",
            "Tagged Field Test Model",
        )
        verbose_name_plural = _(
            "A verbose name",
            "Tagged Field Test Models",
        )

    tagged_field_1 = TagMeCharField(
        max_length=255,
        blank=True,
        null=True,
    )
    tagged_field_2 = TagMeCharField(
        max_length=255,
        blank=True,
        null=True,
    )


class Post(models.Model):
    title = TagMeCharField(
        max_length=255,
        blank=True,
        null=True,
    )
    body = models.TextField()
