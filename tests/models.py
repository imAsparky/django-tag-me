"""tests Models file."""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import pgettext_lazy as _

from tag_me.db.models.fields import TagMeCharField
from tag_me.models import TaggedFieldModel

User = get_user_model()


class TaggedFieldTestModel(models.Model):
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

    tagged_field_1 = TagMeCharField(max_length=255)
    tagged_field_2 = TagMeCharField(max_length=255)
