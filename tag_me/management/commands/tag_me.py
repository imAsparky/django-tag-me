"""Management command for tag-me administration.

Provides subcommands for managing tags, diagnosing issues, and fixing
data integrity problems.

Usage:
    python manage.py tag_me populate [--user USER_ID]
    python manage.py tag_me check [--verbose]
    python manage.py tag_me fix-orphans [--dry-run] [--verbose]
    python manage.py tag_me clear-cache
    python manage.py tag_me help [TOPIC]
"""

import argparse
from uuid import UUID

import structlog
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = structlog.get_logger(__name__)
User = get_user_model()

# =========================================================================
# Help text content — kept here for easy maintenance
# =========================================================================

HELP_OVERVIEW = """\
{heading}Tag-me Administration{reset}

  Manage tags, check data integrity, and fix issues caused by model renames.

{heading}Subcommands{reset}

  {cmd}populate{reset}      Create/update system and user tag records
  {cmd}check{reset}         Audit data integrity and report issues
  {cmd}fix-orphans{reset}   Detect and merge orphaned records from model renames
  {cmd}clear-cache{reset}   Clear Django's ContentType cache
  {cmd}help{reset}          Show this help (or detailed help for a topic)

{heading}Quick Start{reset}

  After renaming a model, run these in order:

    python manage.py tag_me check                      # see what's wrong
    python manage.py tag_me fix-orphans --dry-run      # preview the fix
    python manage.py tag_me fix-orphans                # apply the fix
    python manage.py tag_me check                      # verify it's clean

{heading}Detailed Help{reset}

  python manage.py tag_me help populate
  python manage.py tag_me help check
  python manage.py tag_me help fix-orphans
  python manage.py tag_me help clear-cache
  python manage.py tag_me help rename-workflow
  python manage.py tag_me help troubleshooting
"""

HELP_POPULATE = """\
{heading}tag_me populate{reset}

  Populate or update system and user tag records. This is the same operation
  that runs automatically after every migration via the post_migrate signal.

{heading}Usage{reset}

  python manage.py tag_me populate                # all users
  python manage.py tag_me populate --user 42      # specific user (integer ID)
  python manage.py tag_me populate --user <uuid>  # specific user (UUID)

{heading}What It Does{reset}

  1. Creates/updates {bold}SystemTag{reset} records for fields with tag_type='system'
     - Reflects any changes to field choices
     - Uses update_or_create so existing tags are refreshed

  2. Creates {bold}UserTag{reset} records for fields with tag_type='user'
     - Only creates entries for users who don't have them yet
     - Existing user tags are never overwritten
     - With --user, forces creation for that specific user

{heading}When to Use{reset}

  - After adding new TagMeCharField fields to your models
  - After changing choices on a system tag field
  - After creating new user accounts (runs automatically, but can be forced)
  - After restoring a database backup
"""

HELP_CHECK = """\
{heading}tag_me check{reset}

  Run a comprehensive data integrity audit. Non-destructive — only reads data.

{heading}Usage{reset}

  python manage.py tag_me check                   # summary view
  python manage.py tag_me check --verbose         # detailed breakdown

{heading}What It Checks{reset}

  1. {bold}Orphaned TaggedFieldModel records{reset}
     Records whose ContentType points to a model that no longer exists.
     Caused by model renames (DeleteModel + CreateModel).
     → Fix with: tag_me fix-orphans

  2. {bold}Stale model_name values{reset}
     TaggedFieldModel.model_name doesn't match the current ContentType.model.
     Cosmetic issue — lookups use FKs, not model_name.
     → Fix with: tag_me populate (refreshes cached names)

  3. {bold}UserTag/SystemTag FK integrity{reset}
     Tag records with NULL tagged_field FK (not linked to a TaggedFieldModel).
     → May need manual repair or re-running migrations

  4. {bold}Field name mismatches{reset}
     UserTag.field_name doesn't match its tagged_field.field_name.
     Indicates stale cached data on the UserTag.
     → Fix with: tag_me populate

  5. {bold}Stale ContentTypes{reset}
     ContentType records in tag-me's apps that point to deleted models.
     → Fix with: tag_me fix-orphans (cleans up after merging)

  6. {bold}Summary statistics{reset}
     Total counts of TaggedFieldModel, UserTag, SystemTag, and users.
     With --verbose, shows a per-field breakdown.

{heading}Tip{reset}

  Run {cmd}tag_me check{reset} after any model rename to see if action is needed.
  Run {cmd}tag_me check --verbose{reset} to see every TaggedFieldModel and its tag counts.
"""

HELP_FIX_ORPHANS = """\
{heading}tag_me fix-orphans{reset}

  Detect orphaned TaggedFieldModel records and merge them into their
  replacements, preserving all UserTag and SystemTag relationships.

{heading}Usage{reset}

  python manage.py tag_me fix-orphans --dry-run             # preview only
  python manage.py tag_me fix-orphans --dry-run --verbose   # preview + signatures
  python manage.py tag_me fix-orphans                       # apply changes
  python manage.py tag_me fix-orphans --verbose             # apply + details

{heading}Always preview first!{reset}

  The --dry-run flag shows exactly what will happen without making changes.
  Use --verbose with --dry-run to see the field signature matching logic.

{heading}What It Does{reset}

  1. Finds TaggedFieldModel records whose ContentType points to a deleted model
  2. For each orphan, finds a matching replacement using:

     {bold}Strategy 1: Unique match{reset}
     If only one active TaggedFieldModel exists with the same app_label,
     field_name, and tag_type, it's an unambiguous match.

     {bold}Strategy 2: Field signature matching{reset}
     When multiple candidates exist (e.g., 'emotions' is used in 3 models),
     compares the FULL SET of field names for the orphan's ContentType against
     each candidate's ContentType. The model with the matching field signature
     is the renamed model.

     Example:
       Orphan ContentType (journalposttrade) has fields: {{emotions, other}}
       Candidate journalduringtrade has: {{adjustments, emotions, other}} — no
       Candidate journalpretrade has: {{direction, emotions, ...}} — no
       Candidate journalreviewtrade has: {{emotions, other}} — MATCH ✓

     Falls back to Jaccard similarity if fields were added/removed alongside
     the rename (requires ≥50% overlap and a clear winner).

  3. Migrates UserTag and SystemTag FKs from old → new TaggedFieldModel
     - If a user already has tags on the new record, merges the tag strings
     - If no conflict, re-points the FK directly

  4. Deletes the orphaned TaggedFieldModel record

  5. Cleans up the stale ContentType if no more references exist

{heading}When Merging Fails{reset}

  The command will report "unresolved" orphans when:
  - No candidate exists (model was truly deleted, not renamed)
  - Multiple candidates match and field signatures are identical
  - Missing field_name or app_label on the orphaned record

  For unresolved records, use --verbose to see the field signatures and
  manually determine the correct target. Then fix in the Django shell:

    from tag_me.models import TaggedFieldModel, UserTag
    from django.db import transaction

    old = TaggedFieldModel.objects.get(id=<orphan_id>)
    new = TaggedFieldModel.objects.get(id=<target_id>)

    with transaction.atomic():
        old.user_tags.update(tagged_field=new)
        old.system_tags.update(tagged_field=new)
        old.delete()
"""

HELP_CLEAR_CACHE = """\
{heading}tag_me clear-cache{reset}

  Clear Django's ContentType in-memory cache.

{heading}Usage{reset}

  python manage.py tag_me clear-cache

{heading}Why This Exists{reset}

  Django's ContentType framework caches results in memory. When a model is
  renamed via RenameModel, the migration uses .update() which bypasses this
  cache. If tag-me's save_fields() runs before the cache is invalidated,
  ContentType.objects.get_for_model() may create a DUPLICATE ContentType.

  This is handled automatically during migrations (save_fields clears the
  cache before doing lookups). This command exists for manual use if needed,
  e.g., after running raw SQL or debugging.

{heading}When to Use{reset}

  - Rarely needed manually
  - If 'tag_me check' shows stale ContentTypes after a rename
  - If you suspect ContentType cache issues
  - After manual database operations that modified ContentType records
"""

HELP_RENAME_WORKFLOW = """\
{heading}Model Rename Workflow{reset}

  Step-by-step guide for safely renaming a model that uses TagMeCharField.

{heading}Step 1: Rename the Model{reset}

    # models.py
    class Article(models.Model):          # was: BlogPost
        tags = TagMeCharField()
        category = TagMeCharField(choices=..., system_tag=True)

{heading}Step 2: Make Migrations{reset}

    python manage.py makemigrations

    Django will ask:
      "Did you rename the BlogPost model to Article?"

    {bold}Answer YES.{reset} This generates a RenameModel operation which updates
    the ContentType in place — the cleanest path.

    If Django doesn't ask (happens when other changes are made simultaneously),
    it generates DeleteModel + CreateModel instead. Tag-me handles both, but
    RenameModel is preferred.

{heading}Step 3: Apply Migrations{reset}

    python manage.py migrate

    What happens automatically:
    1. Migration runs (RenameModel or DeleteModel+CreateModel)
    2. post_migrate signal fires
    3. tag-me clears ContentType cache
    4. tag-me registers field metadata (update_or_create by content + field_name)
    5. tag-me runs orphan merger (detects and fixes any orphaned records)
    6. tag-me populates tag records

{heading}Step 4: Verify (Optional){reset}

    python manage.py tag_me check

    Should show "All checks passed — data is healthy"

{heading}If Something Goes Wrong{reset}

    # See what's wrong
    python manage.py tag_me check --verbose

    # Preview the fix
    python manage.py tag_me fix-orphans --dry-run --verbose

    # Apply the fix
    python manage.py tag_me fix-orphans

{heading}How Django Decides: RenameModel vs DeleteModel+CreateModel{reset}

  Django's makemigrations uses a heuristic to detect renames. It compares
  the field signatures of removed and added models. If a model was removed
  and a new model with similar fields was added, Django asks if it's a rename.

  Django is MORE LIKELY to detect the rename when:
  - Only the class name changed (no field changes)
  - The rename is the only change in that makemigrations run

  Django is LESS LIKELY to detect the rename when:
  - Fields were added/removed at the same time
  - Multiple models were renamed simultaneously
  - The model was moved to a different app

  {bold}Best practice:{reset} Rename the model in one commit/migration, then make
  field changes in a separate migration. This maximises Django's chance of
  detecting the rename.
"""

HELP_TROUBLESHOOTING = """\
{heading}Troubleshooting{reset}

{heading}Problem: "Ambiguous — N candidates, field signature did not resolve"{reset}

  This means multiple models in the same app have the exact same set of
  TagMeCharField field names. The automatic matcher can't tell them apart.

  {bold}Diagnosis:{reset}
    python manage.py tag_me fix-orphans --dry-run --verbose

  This shows the field signatures for the orphan and each candidate.
  Identify the correct target manually, then fix in the Django shell:

    from tag_me.models import TaggedFieldModel
    from django.db import transaction

    old = TaggedFieldModel.objects.get(id=<orphan_id>)
    new = TaggedFieldModel.objects.get(id=<correct_target_id>)

    with transaction.atomic():
        old.user_tags.update(tagged_field=new)
        old.system_tags.update(tagged_field=new)
        old.delete()

{heading}Problem: "No matching target found"{reset}

  The model was deleted (not renamed), or the new model doesn't have a
  TagMeCharField with the same field_name.

  If the model was truly deleted and the tags are no longer needed:

    from tag_me.models import TaggedFieldModel
    tfm = TaggedFieldModel.objects.get(id=<orphan_id>)
    tfm.user_tags.all().delete()
    tfm.system_tags.all().delete()
    tfm.delete()

{heading}Problem: Duplicate ContentType after RenameModel{reset}

  This happens when the ContentType cache wasn't cleared. Tag-me now
  clears the cache automatically in save_fields(). To fix existing data:

    python manage.py tag_me clear-cache
    python manage.py tag_me fix-orphans

{heading}Problem: UserTag records with NULL tagged_field FK{reset}

  These are records created before the FK-based lookup was added, or
  records that weren't migrated properly.

  Run migration 0004 to populate them:
    python manage.py migrate tag_me

  If still NULL after migration, check the troubleshooting section in
  the tag-me how-to guide for manual repair instructions.

{heading}Problem: check reports stale model_name values{reset}

  The cached model_name on TaggedFieldModel doesn't match the current
  model name from ContentType. This is cosmetic — lookups use FKs.

  To refresh:
    python manage.py tag_me populate

{heading}Getting More Help{reset}

  python manage.py tag_me help                    # overview
  python manage.py tag_me help populate           # populate details
  python manage.py tag_me help check              # check details
  python manage.py tag_me help fix-orphans        # fix-orphans details
  python manage.py tag_me help clear-cache        # clear-cache details
  python manage.py tag_me help rename-workflow    # full rename guide
  python manage.py tag_me help troubleshooting    # this page

  For issues, open a ticket on the tag-me repository.
"""

HELP_TOPICS = {
    "populate": HELP_POPULATE,
    "check": HELP_CHECK,
    "fix-orphans": HELP_FIX_ORPHANS,
    "clear-cache": HELP_CLEAR_CACHE,
    "rename-workflow": HELP_RENAME_WORKFLOW,
    "troubleshooting": HELP_TROUBLESHOOTING,
}


class Command(BaseCommand):
    help = (
        "Tag-me administration. Subcommands: populate, check, fix-orphans, "
        "clear-cache, help. Run 'manage.py tag_me help' for full usage guide."
    )

    def create_parser(self, prog_name, subcommand, **kwargs):
        """Override to use RawTextHelpFormatter for nicer help text."""
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.formatter_class = argparse.RawTextHelpFormatter
        return parser

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
                        f"'{value}' is not a valid user ID "
                        f"(must be integer or UUID)"
                    )

        parser.add_argument(
            "action",
            type=str,
            choices=[
                "populate",
                "check",
                "fix-orphans",
                "clear-cache",
                "help",
            ],
            help=(
                "Action to perform:\n"
                "  populate     Populate/update system and user tag records\n"
                "  check        Audit data integrity and report issues\n"
                "  fix-orphans  Merge orphaned records from model renames\n"
                "  clear-cache  Clear Django's ContentType cache\n"
                "  help         Show detailed usage guide"
            ),
        )

        parser.add_argument(
            "topic",
            nargs="?",
            default=None,
            help=(
                "(help) Topic to get help on:\n"
                "  populate, check, fix-orphans, clear-cache,\n"
                "  rename-workflow, troubleshooting"
            ),
        )

        parser.add_argument(
            "--user",
            type=user_id_type,
            help="(populate) Target a specific user ID (integer or UUID)",
            metavar="USER_ID",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="(fix-orphans) Preview changes without applying them",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="(check, fix-orphans) Show detailed output",
        )

    def handle(self, *args, **options):
        action = options["action"]

        dispatch = {
            "populate": self._handle_populate,
            "check": self._handle_check,
            "fix-orphans": self._handle_fix_orphans,
            "clear-cache": self._handle_clear_cache,
            "help": self._handle_help,
        }

        handler = dispatch[action]
        handler(**options)

    # =========================================================================
    # HELP
    # =========================================================================

    def _handle_help(self, **options):
        """Display help — overview or detailed topic."""
        topic = options.get("topic")

        if topic and topic in HELP_TOPICS:
            text = HELP_TOPICS[topic]
        elif topic:
            self.stdout.write(
                self.style.ERROR(f"\n  Unknown help topic: '{topic}'\n")
            )
            self.stdout.write("  Available topics:\n")
            for name in HELP_TOPICS:
                self.stdout.write(
                    f"    python manage.py tag_me help {name}"
                )
            self.stdout.write("")
            return
        else:
            text = HELP_OVERVIEW

        self.stdout.write(self._format_help(text))

    def _format_help(self, text):
        """Apply terminal styling to help text."""
        styled = text
        styled = styled.replace("{heading}", "\033[1;36m")  # bold cyan
        styled = styled.replace("{cmd}", "\033[33m")  # yellow
        styled = styled.replace("{bold}", "\033[1m")  # bold
        styled = styled.replace("{reset}", "\033[0m")  # reset
        return f"\n{styled}"

    # =========================================================================
    # POPULATE
    # =========================================================================

    def _handle_populate(self, **options):
        """Populate or update system and user tags."""
        from tag_me.utils.tag_mgmt_system import populate_all_tag_records

        user = None

        if user_id := options.get("user"):
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(
                    self.style.WARNING(
                        f"Targeting specific user: {user.username} "
                        f"(ID: {user_id})"
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"User with ID {user_id} does not exist"
                    )
                )
                return

        try:
            populate_all_tag_records(user=user)

            if user:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Successfully populated tags for "
                        f"user {user.username}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "✓ Successfully populated/updated all tags"
                    )
                )
        except Exception:
            # Library code logs the detail via structlog.
            # Command just reports the failure to stdout.
            self.stdout.write(
                self.style.ERROR(
                    "✗ Tag population failed. Check logs for details."
                )
            )
            raise

    # =========================================================================
    # CHECK
    # =========================================================================

    def _handle_check(self, **options):
        """Audit data integrity and report issues."""
        from django.contrib.contenttypes.models import ContentType

        from tag_me.models import SystemTag, TaggedFieldModel, UserTag

        verbose = options.get("verbose", False)
        issues_found = False

        self.stdout.write(
            self.style.MIGRATE_HEADING("\n  Tag-me Data Integrity Check")
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING("  " + "=" * 40 + "\n")
        )

        # ----- 1. Orphaned TaggedFieldModel records -----
        self.stdout.write(
            "  Checking for orphaned TaggedFieldModel records..."
        )

        orphaned = []
        for tfm in TaggedFieldModel.objects.select_related("content").all():
            if tfm.content is None:
                orphaned.append((tfm, "no ContentType FK"))
            elif tfm.content.model_class() is None:
                orphaned.append((tfm, "model class deleted"))

        if orphaned:
            issues_found = True
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {len(orphaned)} orphaned TaggedFieldModel "
                    f"record(s) found"
                )
            )
            for tfm, reason in orphaned:
                ct_info = (
                    f"{tfm.content.app_label}.{tfm.content.model}"
                    if tfm.content
                    else "None"
                )
                self.stdout.write(
                    f"      id={tfm.id}, model_name='{tfm.model_name}', "
                    f"field_name='{tfm.field_name}', "
                    f"content_type={ct_info} ({reason})"
                )
            self.stdout.write(
                self.style.NOTICE(
                    "    → Fix: python manage.py tag_me fix-orphans"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("    ✓ No orphaned records")
            )

        # ----- 2. Stale model_name values -----
        self.stdout.write("\n  Checking for stale model_name values...")

        stale = []
        for tfm in TaggedFieldModel.objects.select_related("content").all():
            if tfm.content and tfm.content.model_class() is not None:
                current = tfm.content.model
                if tfm.model_name and tfm.model_name.lower() != current:
                    stale.append((tfm, current))

        if stale:
            issues_found = True
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {len(stale)} TaggedFieldModel record(s) "
                    f"with stale model_name"
                )
            )
            for tfm, current in stale:
                self.stdout.write(
                    f"      id={tfm.id}: model_name='{tfm.model_name}' "
                    f"vs content.model='{current}'"
                )
            self.stdout.write(
                self.style.NOTICE(
                    "    → Fix: python manage.py tag_me populate"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "    ✓ All model_name values are current"
                )
            )

        # ----- 3. UserTag / SystemTag FK integrity -----
        self.stdout.write("\n  Checking UserTag FK integrity...")

        null_fk_user = UserTag.objects.filter(
            tagged_field__isnull=True
        ).count()
        if null_fk_user:
            issues_found = True
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {null_fk_user} UserTag record(s) with "
                    f"NULL tagged_field FK"
                )
            )
            if verbose:
                for ut in UserTag.objects.filter(
                    tagged_field__isnull=True
                )[:10]:
                    self.stdout.write(
                        f"      id={ut.id}, user={ut.user_id}, "
                        f"model_name='{ut.model_name}', "
                        f"field_name='{ut.field_name}'"
                    )
                remaining = null_fk_user - 10
                if remaining > 0:
                    self.stdout.write(f"      ... and {remaining} more")
        else:
            self.stdout.write(
                self.style.SUCCESS("    ✓ All UserTag FKs are populated")
            )

        self.stdout.write("\n  Checking SystemTag FK integrity...")

        null_fk_system = SystemTag.objects.filter(
            tagged_field__isnull=True
        ).count()
        if null_fk_system:
            issues_found = True
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {null_fk_system} SystemTag record(s) with "
                    f"NULL tagged_field FK"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("    ✓ All SystemTag FKs are populated")
            )

        # ----- 4. UserTag field_name mismatches -----
        self.stdout.write(
            "\n  Checking for UserTag/TaggedFieldModel "
            "field_name mismatches..."
        )

        mismatches = 0
        for ut in UserTag.objects.select_related("tagged_field").exclude(
            tagged_field__isnull=True
        ):
            if ut.field_name != ut.tagged_field.field_name:
                mismatches += 1
                if verbose:
                    self.stdout.write(
                        f"      UserTag {ut.id}: "
                        f"field_name='{ut.field_name}' vs "
                        f"tagged_field.field_name="
                        f"'{ut.tagged_field.field_name}'"
                    )

        if mismatches:
            issues_found = True
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {mismatches} UserTag record(s) "
                    f"with field_name mismatch"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("    ✓ All field_name values match")
            )

        # ----- 5. Stale ContentTypes -----
        self.stdout.write("\n  Checking for stale ContentTypes...")

        tfm_app_labels = set(
            TaggedFieldModel.objects.select_related("content")
            .values_list("content__app_label", flat=True)
            .distinct()
        )

        stale_cts = []
        for ct in ContentType.objects.filter(app_label__in=tfm_app_labels):
            if ct.model_class() is None:
                stale_cts.append(ct)

        if stale_cts:
            issues_found = True
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ {len(stale_cts)} stale ContentType(s) found"
                )
            )
            for ct in stale_cts:
                ref_count = TaggedFieldModel.objects.filter(
                    content=ct
                ).count()
                self.stdout.write(
                    f"      id={ct.id}, {ct.app_label}.{ct.model} "
                    f"({ref_count} TaggedFieldModel reference(s))"
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("    ✓ No stale ContentTypes")
            )

        # ----- 6. Summary statistics -----
        self.stdout.write(
            self.style.MIGRATE_HEADING("\n  Summary Statistics")
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING("  " + "-" * 40)
        )

        tfm_count = TaggedFieldModel.objects.count()
        ut_count = UserTag.objects.count()
        st_count = SystemTag.objects.count()
        user_count = (
            UserTag.objects.values_list("user_id", flat=True)
            .distinct()
            .count()
        )

        self.stdout.write(f"    TaggedFieldModel records:  {tfm_count}")
        self.stdout.write(f"    UserTag records:           {ut_count}")
        self.stdout.write(f"    SystemTag records:         {st_count}")
        self.stdout.write(f"    Users with tags:           {user_count}")

        if verbose:
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    "\n  TaggedFieldModel Breakdown"
                )
            )
            self.stdout.write(
                self.style.MIGRATE_HEADING("  " + "-" * 40)
            )
            for tfm in (
                TaggedFieldModel.objects.select_related("content").order_by(
                    "content__app_label", "model_name", "field_name"
                )
            ):
                ct_info = (
                    f"{tfm.content.app_label}.{tfm.content.model}"
                    if tfm.content
                    else "NONE"
                )
                ut = tfm.user_tags.count()
                st = tfm.system_tags.count()
                self.stdout.write(
                    f"    {ct_info}.{tfm.field_name} "
                    f"[{tfm.tag_type}] "
                    f"(user_tags={ut}, sys_tags={st})"
                )

        # ----- Final verdict -----
        self.stdout.write("")
        if issues_found:
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠ Issues found — see above for details"
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    "  Run 'python manage.py tag_me help "
                    "troubleshooting' for guidance\n"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✓ All checks passed — data is healthy\n"
                )
            )

    # =========================================================================
    # FIX-ORPHANS
    # =========================================================================

    def _handle_fix_orphans(self, **options):
        """Detect and merge orphaned records from model renames."""
        from collections import defaultdict

        from django.contrib.contenttypes.models import ContentType

        from tag_me.models import TaggedFieldModel
        from tag_me.utils.orphan_merger import (
            _build_field_signatures,
            _resolve_by_field_signature,
        )

        dry_run = options.get("dry_run", False)
        verbose = options.get("verbose", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n  DRY RUN — no changes will be made\n"
                )
            )
        else:
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    "\n  Fix Orphaned TaggedFieldModel Records\n"
                )
            )

        ContentType.objects.clear_cache()

        # Find orphans
        orphaned = []
        for tfm in TaggedFieldModel.objects.select_related("content").all():
            if tfm.content is None:
                orphaned.append(tfm)
            elif tfm.content.model_class() is None:
                orphaned.append(tfm)

        if not orphaned:
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✓ No orphaned TaggedFieldModel records found. "
                    "Data is clean.\n"
                )
            )
            return

        field_signatures = _build_field_signatures(TaggedFieldModel)

        orphans_by_content = defaultdict(list)
        for tfm in orphaned:
            ct_id = tfm.content_id if tfm.content else None
            orphans_by_content[ct_id].append(tfm)

        self.stdout.write(
            f"  Found {len(orphaned)} orphaned TaggedFieldModel record(s) "
            f"across {len(orphans_by_content)} content type(s):\n"
        )

        merged_count = 0
        unresolved_count = 0
        stale_content_types = set()

        for content_id, orphan_group in orphans_by_content.items():
            old_ct = (
                orphan_group[0].content
                if orphan_group[0].content
                else None
            )
            app_label = old_ct.app_label if old_ct else None
            orphan_signature = field_signatures.get(content_id, set())

            if old_ct:
                self.stdout.write(
                    self.style.MIGRATE_HEADING(
                        f"  Content: {old_ct.app_label}.{old_ct.model} "
                        f"(id={content_id})"
                    )
                )
                if verbose:
                    self.stdout.write(
                        f"    Field signature: "
                        f"{sorted(orphan_signature)}"
                    )

            for old_tfm in orphan_group:
                user_tag_count = old_tfm.user_tags.count()
                system_tag_count = old_tfm.system_tags.count()

                self.stdout.write(
                    f"    Orphan: id={old_tfm.id}, "
                    f"field_name='{old_tfm.field_name}', "
                    f"user_tags={user_tag_count}, "
                    f"sys_tags={system_tag_count}"
                )

                if not app_label or not old_tfm.field_name:
                    self.stdout.write(
                        self.style.ERROR(
                            "      ✗ Cannot match — "
                            "missing app_label or field_name"
                        )
                    )
                    unresolved_count += 1
                    continue

                candidates = (
                    TaggedFieldModel.objects.select_related("content")
                    .filter(
                        content__app_label=app_label,
                        field_name=old_tfm.field_name,
                        tag_type=old_tfm.tag_type,
                    )
                    .exclude(id=old_tfm.id)
                )

                valid_candidates = [
                    c
                    for c in candidates
                    if c.content and c.content.model_class() is not None
                ]

                new_tfm = None
                resolution_method = None

                if len(valid_candidates) == 1:
                    new_tfm = valid_candidates[0]
                    resolution_method = "unique match"

                elif len(valid_candidates) > 1:
                    new_tfm = _resolve_by_field_signature(
                        old_tfm,
                        valid_candidates,
                        orphan_signature,
                        field_signatures,
                    )
                    if new_tfm:
                        resolution_method = "field signature"

                if new_tfm:
                    if verbose:
                        candidate_sig = field_signatures.get(
                            new_tfm.content_id, set()
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"      → Match ({resolution_method}): "
                                f"'{new_tfm.model_name}."
                                f"{new_tfm.field_name}' "
                                f"(id={new_tfm.id})"
                            )
                        )
                        self.stdout.write(
                            f"        Target signature: "
                            f"{sorted(candidate_sig)}"
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"      → Match: '{new_tfm.model_name}."
                                f"{new_tfm.field_name}' "
                                f"({resolution_method})"
                            )
                        )

                    if not dry_run:
                        # The merge itself logs via structlog in
                        # orphan_merger.py. Command just shows stdout.
                        self._merge_one(
                            old_tfm, new_tfm, verbose=verbose
                        )
                    else:
                        self.stdout.write(
                            f"      [DRY RUN] Would migrate "
                            f"{user_tag_count} UserTag(s), "
                            f"{system_tag_count} SystemTag(s)"
                        )

                    merged_count += 1
                    if old_ct:
                        stale_content_types.add(old_ct)

                elif len(valid_candidates) == 0:
                    self.stdout.write(
                        self.style.ERROR(
                            "      ✗ No matching target found — "
                            "manual intervention needed"
                        )
                    )
                    self.stdout.write(
                        self.style.NOTICE(
                            "        Run 'python manage.py tag_me "
                            "help troubleshooting' for guidance"
                        )
                    )
                    unresolved_count += 1

                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"      ✗ Ambiguous — "
                            f"{len(valid_candidates)} candidates, "
                            f"field signature did not resolve:"
                        )
                    )
                    for c in valid_candidates:
                        c_sig = field_signatures.get(
                            c.content_id, set()
                        )
                        self.stdout.write(
                            f"        {c.model_name} (id={c.id}) "
                            f"signature={sorted(c_sig)}"
                        )
                    self.stdout.write(
                        f"        orphan signature="
                        f"{sorted(orphan_signature)}"
                    )
                    self.stdout.write(
                        self.style.NOTICE(
                            "        Run 'python manage.py tag_me "
                            "help troubleshooting' for guidance"
                        )
                    )
                    unresolved_count += 1

        # Clean up stale ContentTypes
        for stale_ct in stale_content_types:
            remaining = TaggedFieldModel.objects.filter(
                content=stale_ct
            ).count()
            if remaining == 0:
                if dry_run:
                    self.stdout.write(
                        f"\n    [DRY RUN] Would delete stale "
                        f"ContentType: {stale_ct.app_label}."
                        f"{stale_ct.model} (id={stale_ct.id})"
                    )
                else:
                    stale_ct.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n    ✓ Deleted stale ContentType: "
                            f"{stale_ct.app_label}.{stale_ct.model} "
                            f"(id={stale_ct.id})"
                        )
                    )

        # Summary
        self.stdout.write(
            f"\n  Summary: {merged_count} merged, "
            f"{unresolved_count} unresolved"
        )

        if dry_run and merged_count > 0:
            self.stdout.write(
                self.style.NOTICE(
                    "\n  Re-run without --dry-run to apply changes:\n"
                    "    python manage.py tag_me fix-orphans\n"
                )
            )
        elif not dry_run and merged_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n  ✓ Successfully merged {merged_count} "
                    f"orphaned record(s)\n"
                )
            )
        if unresolved_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n  ⚠ {unresolved_count} record(s) need "
                    f"manual intervention."
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    "  Run 'python manage.py tag_me help "
                    "troubleshooting' for guidance\n"
                )
            )

    def _merge_one(self, old_tfm, new_tfm, verbose=False):
        """Merge a single orphaned TaggedFieldModel into its replacement."""
        from django.db import transaction

        from tag_me.models import SystemTag, UserTag
        from tag_me.utils.orphan_merger import _merge_tag_strings

        with transaction.atomic():
            ut_migrated = 0
            ut_merged = 0

            for old_ut in old_tfm.user_tags.all():
                existing = UserTag.objects.filter(
                    user=old_ut.user,
                    tagged_field=new_tfm,
                ).first()

                if existing:
                    if old_ut.tags and old_ut.tags.strip():
                        _merge_tag_strings(
                            source=old_ut, target=existing
                        )
                        existing.save()
                    old_ut.delete()
                    ut_merged += 1
                else:
                    old_ut.tagged_field = new_tfm
                    old_ut.model_name = new_tfm.model_name
                    old_ut.model_verbose_name = new_tfm.model_verbose_name
                    old_ut.save()
                    ut_migrated += 1

            st_migrated = 0
            st_merged = 0

            for old_st in old_tfm.system_tags.all():
                existing = SystemTag.objects.filter(
                    tagged_field=new_tfm,
                ).first()

                if existing:
                    old_st.delete()
                    st_merged += 1
                else:
                    old_st.tagged_field = new_tfm
                    old_st.model_name = new_tfm.model_name
                    old_st.model_verbose_name = new_tfm.model_verbose_name
                    old_st.save()
                    st_migrated += 1

            old_tfm.delete()

        if verbose:
            self.stdout.write(
                f"      ✓ UserTags: {ut_migrated} migrated, "
                f"{ut_merged} merged"
            )
            self.stdout.write(
                f"      ✓ SystemTags: {st_migrated} migrated, "
                f"{st_merged} merged"
            )
        else:
            total = ut_migrated + ut_merged + st_migrated + st_merged
            self.stdout.write(
                self.style.SUCCESS(
                    f"      ✓ Migrated {total} tag record(s), "
                    f"deleted orphan"
                )
            )

    # =========================================================================
    # CLEAR-CACHE
    # =========================================================================

    def _handle_clear_cache(self, **options):
        """Clear Django's ContentType cache."""
        from django.contrib.contenttypes.models import ContentType

        ContentType.objects.clear_cache()

        self.stdout.write(
            self.style.SUCCESS(
                "\n  ✓ ContentType cache cleared.\n\n"
                "  This is useful after model renames to ensure tag-me "
                "sees\n"
                "  the updated ContentType records. Normally this happens\n"
                "  automatically during migrations.\n"
            )
        )
