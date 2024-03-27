"""Management command to update the Tagged Field Models table."""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand, LabelCommand

from tag_me.utils.helpers import update_models_with_tagged_fields_table

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        """
        Handles the execution of tag-related updates and synchronization checks.

        This method performs the following:
            1. Logs the start of the update process.
            2. Updates the 'TaggedFieldModel' table for tag management.
            3. Checks and updates field synchronization configurations.
            4. Reports any errors encountered during the update process.

        :param args: Additional positional arguments.
        :param options: Additional keyword arguments.
        """
        logger.info("Updating Tagged Models Table, and Synchronised Fields.")

        try:
            self.stdout.write("    Updating Tagged Models Table.")
            update_models_with_tagged_fields_table()
            self.stdout.write(
                self.style.SUCCESS(
                    "    SUCCESS: Tagged Models Table,"
                    " and Synchronised Fields updated."
                )
            )
        except Exception as e:
            logger.error(
                "Tags Table Update Error",
                exc_info=True,
            )
            self.stdout.write(
                self.style.ERROR(
                    "    ERROR: Tagged Models Table, and "
                    " Synchronised Fields not updated."
                )
            )

        finally:
            # Ensure synchronization configuration check is performed and logged.
            from tag_me.models import TagMeSynchronise

            sync, _ = TagMeSynchronise.objects.get_or_create(name="default")
            sync.check_field_sync_list_lengths()
