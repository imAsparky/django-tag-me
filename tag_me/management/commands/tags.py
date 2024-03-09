"""Management command to update the Tagged Field Models table."""

import logging

from django.core.management.base import BaseCommand, LabelCommand

#  from tag_me.utils.helpers import update_models_with_tagged_fields_table

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        logger.info("Updating Tagged Models Table.")

        # try:
        #     self.stdout.write("    Updating Tagged Models Table.")
        #     update_models_with_tagged_fields_table()
        #     self.stdout.write("    SUCCESS: Tagged Models Table updated.")
        # except Exception as e:
        #     logger.error(
        #         "Tags Table Update Error",
        #         exc_info=True,
        #     )
        #     self.stdout.write("    ERROR: Tagged Models Table not updated.")
