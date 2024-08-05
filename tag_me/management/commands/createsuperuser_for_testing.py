"""Create a superuser programmatically for testing."""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Create a superuser if username doesn't exist Example: ./manage.py
    createsuperuser_for_testing --username=test_user
    --password=test_password --email=test_user@email.com
    """

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument("--delete", default=False)

    def handle(self, *args, **options):
        User = get_user_model()

        if options["delete"]:
            if not User.objects.filter(username=options["username"]).exists():
                print(f"This username {options['username']} does not exist.")
                return
            try:
                u = User.objects.get(username=options["username"])
                u.delete()
            except Exception:
                logger = logging.getLogger(__name__)
                logger.error("Failed to delete the testing superuser.")
            finally:
                if not User.objects.filter(
                    username=options["username"]
                ).exists():
                    print(
                        f"This username {options['username']} was deleted successfully."  # noqa: E501
                    )
                    return
        else:
            if User.objects.filter(username=options["username"]).exists():
                print(f"This username {options['username']} exists.")
                return
            try:
                User.objects.create_superuser(
                    username=options["username"],
                    password=options["password"],
                    email=options["email"],
                )
            except Exception:
                logger = logging.getLogger(__name__)
                logger.error("Failed to create the testing superuser.")
            finally:
                if User.objects.filter(username=options["username"]).exists():
                    print(
                        f"This username {options['username']} was created successfully."  # noqa: E501
                    )
                    return
