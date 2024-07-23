"""Management command to add user Tagged Fields to the usertag table."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, LabelCommand

from tag_me.models import TagBase, TaggedFieldModel, UserTag

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Update UserTag objects for all users and tagged fields."

    def handle(self, *args, **options):
        try:
            # Get all unique users from UserTag
            existing_user_ids = UserTag.objects.values_list(
                "user_id", flat=True
            ).distinct()

            # Get all users who are NOT in existing_user_ids
            users = User.objects.exclude(id__in=existing_user_ids)
            tagged_fields = TaggedFieldModel.objects.all()

            self.stdout.write("    Updating UserTag table...")

            user_tags = []
            for user in users:
                tags = f"tag1-{user.id}"
                for field in tagged_fields:
                    user_tags.append(
                        UserTag(
                            user=user,
                            tagged_field=field,
                            model_verbose_name=field.model_verbose_name,
                            field_name=field.field_name,
                            field_verbose_name=field.field_verbose_name,
                            slug=TagBase.slugify(tag=str(user.id)),
                            tags=tags,
                        )
                    )
            # Bulk create UserTag objects
            UserTag.objects.bulk_create(
                user_tags, ignore_conflicts=False
            )  # Optional: Handle existing tags

            self.stdout.write(
                self.style.SUCCESS(
                    f"    SUCCESS: UserTag table created {len(user_tags)} new user tag records for {users.count()} new users."
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"ERROR: Failed to update UserTag table: {e}")
            )


# class Command(BaseCommand):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#     def handle(self, *args, **options):
#         """
#         Handles the execution of tag-related updates and synchronization checks.
#
#         This method performs the following:
#             1. Logs the start of the update process.
#             2. Updates the 'TaggedFieldModel' table for tag management.
#             3. Checks and updates field synchronization configurations.
#             4. Reports any errors encountered during the update process.
#
#         :param args: Additional positional arguments.
#         :param options: Additional keyword arguments.
#         """
#         logger.info("Updating UserTag Models Table.")
#
#         try:
#             users = User.objects.all()
#             fields = TaggedFieldModel.objects.all()
#             self.stdout.write("    Updating Tagged Models Table.")
#             for field in fields:
#                 print(f"MGMT FIELD {field}")
#                 t = UserTag.objects.update_or_create(
#                     user=User.objects.first(),
#                     tagged_field=field,
#                     model_verbose_name=field.model_verbose_name,
#                     field_verbose_name=field.field_verbose_name,
#                 )
#                 print(f"ADDED TAG LINE {t}")
#             self.stdout.write(
#                 self.style.SUCCESS(
#                     "    SUCCESS: Tagged Models Table,"
#                     " and Synchronised Fields updated."
#                 )
#             )
#         except Exception as e:
#             logger.error(
#                 "Tags Table Update Error",
#                 exc_info=True,
#             )
#             self.stdout.write(
#                 self.style.ERROR(
#                     "    ERROR: Tagged Models Table, and "
#                     " Synchronised Fields not updated."
#                 )
#             )
#
# finally:
#     # Ensure synchronization configuration check is performed and logged.
#     from tag_me.models import TagMeSynchronise
#
#     sync, _ = TagMeSynchronise.objects.get_or_create(name="default")
#     sync.check_field_sync_list_lengths()
