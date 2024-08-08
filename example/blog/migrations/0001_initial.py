# Generated by Django 5.0.7 on 2024-08-08 06:28

import tag_me.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Article",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("article", models.TextField(verbose_name="Article")),
                (
                    "tag",
                    tag_me.db.models.fields.TagMeCharField(
                        blank=True,
                        help_text="A tag for the Article",
                        max_length=255,
                        null=True,
                        verbose_name="Article Tag",
                    ),
                ),
                (
                    "user_tag",
                    tag_me.db.models.fields.TagMeCharField(
                        blank=True,
                        help_text="A tag for the Article",
                        max_length=255,
                        null=True,
                        verbose_name="Article User Tag",
                    ),
                ),
                (
                    "user_tag2",
                    tag_me.db.models.fields.TagMeCharField(
                        blank=True,
                        help_text="A tag2 for the Article",
                        max_length=255,
                        null=True,
                        verbose_name="Article User Tag 2",
                    ),
                ),
            ],
            options={
                "verbose_name": "Blog Article",
                "verbose_name_plural": "Blog Articles",
            },
        ),
        migrations.CreateModel(
            name="Author",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "pen_name",
                    models.CharField(max_length=255, verbose_name="Author"),
                ),
                (
                    "bio",
                    models.TextField(
                        blank=True, null=True, verbose_name="Biography"
                    ),
                ),
            ],
            options={
                "verbose_name": "Author",
                "verbose_name_plural": "Authors",
            },
        ),
    ]
