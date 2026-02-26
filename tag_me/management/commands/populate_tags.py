"""Backward-compatible alias for 'python manage.py tag_me populate'.

This command is kept for backward compatibility. New code should use:
    python manage.py tag_me populate [--user USER_ID]

See 'python manage.py tag_me help' for all available subcommands.
"""

import argparse
import warnings
from uuid import UUID

import structlog
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tag_me.utils.tag_mgmt_system import populate_all_tag_records

logger = structlog.get_logger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = (
        "DEPRECATED: Use 'python manage.py tag_me populate' instead.\n"
        "Populate or update tag-me system and user tags."
    )

    def add_arguments(self, parser):
        def user_id_type(value):
            """Accept both integer and UUID formats."""
            try:
                return UUID(value)
            except ValueError:
                try:
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
        warnings.warn(
            "populate_tags is deprecated. "
            "Use 'python manage.py tag_me populate' instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        user = None

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
        except Exception:
            self.stdout.write(
                self.style.ERROR("✗ Tag population failed. Check logs for details.")
            )
            raise

