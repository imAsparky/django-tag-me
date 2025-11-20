"""Management command to populate and update tag-me system and user tags."""

import argparse
import logging
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tag_me.utils.tag_mgmt_system import populate_all_tag_records

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = (
        "Populate or update tag-me system and user tags. "
        "System tags are updated to reflect any field/choice changes. "
        "User tags are only created for new users. "
        "This normally runs automatically after migrate."
    )

    def add_arguments(self, parser):
        def user_id_type(value):
            """Accept both integer and UUID formats."""
            try:
                # Try UUID first
                return UUID(value)
            except ValueError:
                try:
                    # Fall back to integer
                    return int(value)
                except ValueError:
                    raise argparse.ArgumentTypeError(
                        f"'{value}' is not a valid user ID (must be integer or UUID)"
                    )

        parser.add_argument(
            "--user",
            type=user_id_type,
            help="Populate tags for a specific user ID (integer or UUID)",
            metavar="USER_ID",
        )

    def handle(self, *args, **options):
        """Execute the tag population process."""
        user = None

        # Handle specific user if provided
        if user_id := options.get("user"):
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(
                    self.style.WARNING(
                        f"Targeting specific user: {user.username} (ID: {user_id})"
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with ID {user_id} does not exist")
                )
                return

        try:
            populate_all_tag_records(user=user)
            if user:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Successfully populated tags for user {user.username}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✓ Successfully populated/updated all tags")
                )
        except Exception as e:
            logger.exception("Tag population failed")
            self.stdout.write(
                self.style.ERROR(
                    f"✗ Tag population failed: {str(e)}\n"
                    "  Check logs for full error details."
                )
            )
            # Re-raise to ensure non-zero exit code
            raise
