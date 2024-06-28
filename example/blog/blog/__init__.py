import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Reset the blog database, apply migrations, and load seed data."

    def handle(self, *args, **options):
        # 1. Delete the existing database file
        db_file = connection.settings_dict["NAME"]  # Get database file path
        if os.path.exists(db_file):
            os.remove(db_file)
            self.stdout.write(self.style.SUCCESS("Deleted existing database."))

        # 2. Apply migrations
        call_command("migrate")
        self.stdout.write(
            self.style.SUCCESS("Migrations applied successfully.")
        )

        # 3. Load fixture data
        fixture_path = "blog/management/fixtures/tag_me_fixtures.json"
        call_command("loaddata", fixture_path)
        self.stdout.write(self.style.SUCCESS("Fixture data loaded."))
