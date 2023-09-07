"""Management command to update the Tagged Field Models table."""
import logging

from django.core.management.base import LabelCommand

from tag_me.utils.helpers import update_models_with_tagged_fields_table

logger = logging.getLogger(__name__)


class Command(LabelCommand):
    help = "Update Tagged Fields Table"
    missing_args_message = """
    \nA command argument is missing, please add one of the following:
        -U  or --update : Updates the Tagged Field Models Table

    Usage examples:
        python manage.py tags -U
        python manage.py tags --update

"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "-U",
            "--update",
            action="store_true",
            help="Update Tagged Field Models table.",
        )

    def handle(self, *args, **options):
        if options["update"]:
            logger.info("\n\n***** Updating Tagged Models *****\n")

            update_models_with_tagged_fields_table()
