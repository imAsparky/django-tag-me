"""Management command to update the Tagged Field Models table."""

import logging

from django.core.management.base import BaseCommand

from tag_me.utils.tag_mgmt_system import (
    populate_all_tag_records,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        """ """

        try:
            populate_all_tag_records()
        except Exception:
            logger.exception(
                "Tags Table Update Error",
                exc_info=True,
            )
            self.stdout.write(
                self.style.ERROR(
                    "    ERROR: Tagged Models Table, and "
                    " Synchronised Fields not updated."
                )
            )
