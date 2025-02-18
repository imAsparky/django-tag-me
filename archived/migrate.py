# """Custom migrate command"""
#
# import logging
# import subprocess
# from io import StringIO
#
# from django.conf import settings
# from django.core.management import call_command
# from django.core.management.commands.migrate import (
#     Command as CoreMigrateCommand,
# )
#
# logger = logging.getLogger(__name__)
#
#
# class Command(CoreMigrateCommand):
#     """Override `migrate.py` to run the `tag_me` tables update command.
#
#     Call the tags management command after migrate.
#     tag_me management command `tags.py` checks all models and adds any with
#     tag fields to `TaggedFieldModel` table.
#     """
#
#     def handle(self, *args, **options):
#         super().handle(*args, **options)
#         out = StringIO()
#         call_command(
#             "tags",
#             stdout=out,
#         )
#         return out.getvalue()
#
#         # def handle(self, *args, **options):
#         if settings.DJ_TAG_ME_USE_CUSTOM_MIGRATE:
#             super().handle(*args, **options)
#
#     #
#     #     err = None
#     #     out = None
#     #
#     #     try:
#     #         with subprocess.Popen(  # nosec
#     #             args=["./manage.py", "tags"],
#     #             stdout=subprocess.PIPE,
#     #             stderr=subprocess.PIPE,
#     #             bufsize=0,
#     #             text=True,
#     #             encoding="utf-8",
#     #         ) as proc:
#     #             out, err = proc.communicate(timeout=10)
#     #
#     #             logger.info(f"Process Successful: {args}\n{out}")
#     #
#     #     except subprocess.TimeoutExpired:
#     #         logger.error(f"{args} error: {err}")
#     #         logger.error("Exiting migrate!")
#     #         raise SystemExit(1)
#     #
#     #     except subprocess.CalledProcessError as e:
#     #         logger.error(
#     #             f"{args} failed with return code {proc.returncode}.\nError {e}"
#     #         )
#     #         logger.error("Exiting nuke_db_sqlite")
#     #         raise SystemExit(1)
#     #
#     #     except OSError as e:
#     #         print(f"ERROR IS {e}")
#     #         logger.error(f"{args} failed with return code.\nError{e}")
#     #         logger.error("Exiting nuke_db_sqlite")
#     #         raise SystemExit(1)
#     #
#     #     except ValueError as e:
#     #         logger.error(f"{args} failed with return code {proc.returncode}.\nError{e}")
#     #         logger.error("Exiting nuke_db_sqlite")
#     #         raise SystemExit(1)
#     #
#     #     # return out
#     #
#     #     # logger.error("######### TAGS MIGRATE")
#     #     # if settings.DJ_TAG_ME_USE_CUSTOM_MIGRATE:
#     #     #     super().handle(*args, **options)
#     #     # out = StringIO()
#     #     # call_command(
#     #     #     "tags",
#     #     #     stdout=out,
#     #     # )
#     #     #
#     #     # return out.getvalue()
