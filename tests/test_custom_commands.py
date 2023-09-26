from io import StringIO

from django.core.management import call_command
from hypothesis.extra.django import TestCase


class TestCustomManagementCommands(TestCase):
    def test_custom_migrate_command_ok(self):
        self.out_migration = StringIO()
        call_command(
            "migrate",
            stdout=self.out_migration,
        )

        assert "Updating Tagged Models Table." in self.out_migration.getvalue()
        assert (
            "SUCCESS: Tagged Models Table updated."
            in self.out_migration.getvalue()
        )
