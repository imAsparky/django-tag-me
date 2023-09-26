"""Custom migrate command"""
from io import StringIO

from django.core.management import call_command
from django.core.management.commands.migrate import Command as CoreMigrateCommand


class Command(CoreMigrateCommand):
    """Override `migrate.py` to run the `tag_me` tables update command.

    Call the tags management command after migrate.
    tag_me management command `tags.py` checks all models and adds any with
    tag fields to `TaggedFieldModel` table.
    """

    def handle(self, *args, **options):
        super().handle(*args, **options)

        out = StringIO()
        call_command(
            "tags",
            stdout=out,
        )
        return out.getvalue()
