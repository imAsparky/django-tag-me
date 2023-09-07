import subprocess

from django.conf import settings
from django.core.management.commands.migrate import (
    Command as CoreMigrateCommand,
)


class Command(CoreMigrateCommand):
    """Over ride `migrate.py` to run the `tag_me` tables update command.

    Overrides the  handle function, adds a subprocess running `./manage.py tags -U`.


    .. caution::

        The subprocess running tags table updates is disabled when running tests.

        This is so in-memory testing can be used to increase the speed of the test suite.

        If the override is not in place a `content_type` `table does not exist` exception
        is raised and testing fails.

        If testing is selected, a warning message is printed to logging stdout alerting the
        user.

    """

    def handle(self, *args, **options):
        super().handle(*args, **options)

        if "test" in settings.SETTINGS_MODULE.lower():
            import logging

            logger = logging.getLogger(__name__)

            logger.warning(
                "\n\n\t***** Tags update tagged field table modified for testing!\n\t***** Disabling allows use of in memory testing...\n"
            )

        with subprocess.Popen(  # nosec
            ["./manage.py", "tags", "-U"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            out, err = proc.communicate()
            out = out.decode("utf-8")
            err = err.decode("utf-8")
            # 19-6-2023 added testing check. Can be revisited, using to fix a pip bug
            # deprecation warning in test dep.
            if "test" not in settings.SETTINGS_MODULE.lower():
                if err:
                    raise Exception(err)
                if err:
                    return out

            return out
