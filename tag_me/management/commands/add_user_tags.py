"""Management command to update the Tagged Field Models table."""

import logging

from django.core.management.base import BaseCommand, LabelCommand

from tag_me.utils.tag_mgmt_system import (
    generate_user_tag_table_records,
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        """ """

        try:
            generate_user_tag_table_records()
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
