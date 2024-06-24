"""django-tag-me article models"""

from django.db import models
from tag_me.db.models.fields import TagMeCharField
from django.contrib.auth.models import AbstractUser
from django.utils.translation import pgettext_lazy as _
from django.contrib.auth.models import User
# class BlogUser(AbstractUser):
#     pass


class Author(models.Model):
    """Author model"""

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Author",
    )

    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name="Biography",
    )


class Article(models.Model):
    """Article model"""

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    class ArticleTags(models.TextChoices):
        """An example using choices to constrain tag list"""

        TWOMINREAD = (
            "2 Min Read",
            _(
                "Article Tag",
                "2 Min Read",
            ),
        )
        FIVEMINREAD = (
            "5 Min Read",
            _(
                "Article Tag",
                "5 Min Read",
            ),
        )

    author = models.ForeignKey(
        "Author",
        on_delete=models.CASCADE,
        verbose_name="Article Author",
    )

    article = models.TextField(
        verbose_name="Article",
    )
    tag = TagMeCharField(
        max_length=255,
        null=True,
        blank=True,
        choices=ArticleTags.choices,
        verbose_name="Article Tag",
        help_text="A tag for the Article",
    )
