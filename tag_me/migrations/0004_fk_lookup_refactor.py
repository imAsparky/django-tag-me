# Generated migration for FK-based lookup refactor
#
# This migration completes the FK-based lookup refactor by:
# - Checking for duplicates before adding constraint
# - Adding the unique constraint on TaggedFieldModel (content + field_name)
# - Populating tagged_field FK on existing UserTag/SystemTag records
# - Updating help_text on model_name fields
# - Adding performance indexes
#
# NOTE: The tagged_field FK columns were already added in migrations 0002/0003.
# This migration only populates them and adds supporting changes.

from django.db import migrations, models
import django.db.models.deletion


def check_for_duplicates(apps, schema_editor):
    """
    Pre-check: Ensure no duplicate (content, field_name) pairs exist.

    If duplicates exist, the AddConstraint will fail. Better to fail early
    with a helpful message than to fail cryptically.
    """
    TaggedFieldModel = apps.get_model("tag_me", "TaggedFieldModel")
    from django.db.models import Count

    duplicates = list(
        TaggedFieldModel.objects.values("content_id", "field_name")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )

    if duplicates:
        # Get details for error message
        dup_details = []
        for dup in duplicates[:5]:  # Show first 5
            records = TaggedFieldModel.objects.filter(
                content_id=dup["content_id"], field_name=dup["field_name"]
            ).values_list("id", "model_name")
            dup_details.append(
                f"  - content_id={dup['content_id']}, field_name='{dup['field_name']}': "
                f"IDs {list(records)}"
            )

        if len(duplicates) > 5:
            dup_details.append(f"  ... and {len(duplicates) - 5} more")

        raise Exception(
            f"\n{'=' * 60}\n"
            f"MIGRATION BLOCKED: Duplicate TaggedFieldModel records found!\n"
            f"{'=' * 60}\n\n"
            f"The following (content, field_name) combinations have duplicates:\n"
            f"{chr(10).join(dup_details)}\n\n"
            f"Please resolve these duplicates before upgrading:\n"
            f"1. Identify which record should be kept\n"
            f"2. Update any UserTag/SystemTag records pointing to duplicates\n"
            f"3. Delete the duplicate records\n"
            f"4. Re-run migrations\n\n"
            f"See tag-me documentation for detailed instructions.\n"
            f"{'=' * 60}\n"
        )


def populate_user_tag_fk(apps, schema_editor):
    """
    Populate UserTag.tagged_field FK using multiple matching strategies.

    Handles cases where:
    - model_name matches exactly (normal case)
    - model was renamed and model_name diverged (ContentType.model matches)
    - field_name is unique across all models (unambiguous match)
    """
    UserTag = apps.get_model("tag_me", "UserTag")
    TaggedFieldModel = apps.get_model("tag_me", "TaggedFieldModel")

    # Get all UserTags needing FK population
    user_tags_to_update = list(
        UserTag.objects.filter(tagged_field__isnull=True).values_list(
            "id", "model_name", "model_verbose_name", "field_name", "field_verbose_name"
        )
    )

    if not user_tags_to_update:
        print("UserTag: No records needed FK population.")
        return

    # Build lookup caches for efficiency
    tfm_by_model_field = {}
    tfm_by_content_field = {}
    tfm_by_verbose_field = {}
    tfm_by_field_verbose = {}
    tfm_by_field_only = {}

    for tfm in TaggedFieldModel.objects.select_related("content").all():
        # Skip records without field_name - can't match them
        if tfm.field_name is None:
            continue

        # Strategy 1 cache: model_name + field_name
        if tfm.model_name:
            key1 = (tfm.model_name, tfm.field_name)
            tfm_by_model_field[key1] = tfm

        # Strategy 2 cache: content.model (lowercase) + field_name
        if tfm.content:
            key2 = (tfm.content.model, tfm.field_name)
            tfm_by_content_field[key2] = tfm

        # Strategy 3 cache: model_verbose_name + field_name
        if tfm.model_verbose_name:
            key3 = (tfm.model_verbose_name, tfm.field_name)
            tfm_by_verbose_field[key3] = tfm

        # Strategy 4 cache: field_name + field_verbose_name
        if tfm.field_verbose_name:
            key4 = (tfm.field_name, tfm.field_verbose_name)
            if key4 not in tfm_by_field_verbose:
                tfm_by_field_verbose[key4] = [tfm]
            else:
                tfm_by_field_verbose[key4].append(tfm)

        # Strategy 5 cache: field_name only
        if tfm.field_name not in tfm_by_field_only:
            tfm_by_field_only[tfm.field_name] = [tfm]
        else:
            tfm_by_field_only[tfm.field_name].append(tfm)

    updated = 0
    failed = []
    updates_to_apply = []  # List of (ut_id, tfm_id)

    for (
        ut_id,
        model_name,
        model_verbose_name,
        field_name,
        field_verbose_name,
    ) in user_tags_to_update:
        tagged_field = None

        # Skip if no field_name - can't match
        if not field_name:
            failed.append(
                {
                    "id": ut_id,
                    "model_name": model_name,
                    "field_name": field_name,
                    "reason": "No field_name",
                }
            )
            continue

        # Strategy 1: Exact match by model_name + field_name
        if model_name:
            tagged_field = tfm_by_model_field.get((model_name, field_name))

        # Strategy 2: Match by ContentType.model (lowercase) + field_name
        if not tagged_field and model_name:
            tagged_field = tfm_by_content_field.get((model_name.lower(), field_name))

        # Strategy 3: Match by model_verbose_name + field_name
        if not tagged_field and model_verbose_name:
            tagged_field = tfm_by_verbose_field.get((model_verbose_name, field_name))

        # Strategy 4: Match by field_name + field_verbose_name (if unambiguous)
        if not tagged_field and field_verbose_name:
            candidates = tfm_by_field_verbose.get((field_name, field_verbose_name), [])
            if len(candidates) == 1:
                tagged_field = candidates[0]

        # Strategy 5: Match by field_name only (if globally unique)
        if not tagged_field:
            candidates = tfm_by_field_only.get(field_name, [])
            if len(candidates) == 1:
                tagged_field = candidates[0]

        if tagged_field:
            updates_to_apply.append((ut_id, tagged_field.id))
            updated += 1
        else:
            failed.append(
                {
                    "id": ut_id,
                    "model_name": model_name,
                    "field_name": field_name,
                    "reason": "No matching TaggedFieldModel",
                }
            )

    # Apply updates using Django ORM (safe for all database backends)
    # Wrapped in transaction for atomicity
    if updates_to_apply:
        from django.db import transaction

        with transaction.atomic():
            for ut_id, tfm_id in updates_to_apply:
                UserTag.objects.filter(id=ut_id).update(tagged_field_id=tfm_id)

    if failed:
        print(f"\n{'=' * 60}")
        print(
            f"WARNING: Could not find TaggedFieldModel for {len(failed)} UserTag records:"
        )
        for f in failed[:10]:
            print(
                f"  - UserTag {f['id']}: {f['model_name']}.{f['field_name']} ({f.get('reason', 'unknown')})"
            )
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
        print("\nThese records may reference models that were renamed or deleted.")
        print("See tag-me documentation for manual repair instructions.")
        print(f"{'=' * 60}\n")

    if updated:
        print(f"Populated tagged_field FK for {updated} UserTag record(s).")


def populate_system_tag_fk(apps, schema_editor):
    """
    Populate SystemTag.tagged_field FK using multiple matching strategies.

    Uses same caching strategy as UserTag for efficiency.
    """
    SystemTag = apps.get_model("tag_me", "SystemTag")
    TaggedFieldModel = apps.get_model("tag_me", "TaggedFieldModel")

    # Get all SystemTags needing FK population
    system_tags_to_update = list(
        SystemTag.objects.filter(tagged_field__isnull=True).values_list(
            "id", "model_name", "model_verbose_name", "field_name", "field_verbose_name"
        )
    )

    if not system_tags_to_update:
        print("SystemTag: No records needed FK population.")
        return

    # Build lookup caches (same as UserTag)
    tfm_by_model_field = {}
    tfm_by_content_field = {}
    tfm_by_verbose_field = {}
    tfm_by_field_verbose = {}
    tfm_by_field_only = {}

    for tfm in TaggedFieldModel.objects.select_related("content").all():
        # Skip records without field_name - can't match them
        if tfm.field_name is None:
            continue

        if tfm.model_name:
            key1 = (tfm.model_name, tfm.field_name)
            tfm_by_model_field[key1] = tfm

        if tfm.content:
            key2 = (tfm.content.model, tfm.field_name)
            tfm_by_content_field[key2] = tfm

        if tfm.model_verbose_name:
            key3 = (tfm.model_verbose_name, tfm.field_name)
            tfm_by_verbose_field[key3] = tfm

        if tfm.field_verbose_name:
            key4 = (tfm.field_name, tfm.field_verbose_name)
            if key4 not in tfm_by_field_verbose:
                tfm_by_field_verbose[key4] = [tfm]
            else:
                tfm_by_field_verbose[key4].append(tfm)

        if tfm.field_name not in tfm_by_field_only:
            tfm_by_field_only[tfm.field_name] = [tfm]
        else:
            tfm_by_field_only[tfm.field_name].append(tfm)

    updated = 0
    failed = []
    updates_to_apply = []

    for (
        st_id,
        model_name,
        model_verbose_name,
        field_name,
        field_verbose_name,
    ) in system_tags_to_update:
        tagged_field = None

        # Skip if no field_name - can't match
        if not field_name:
            failed.append(
                {
                    "id": st_id,
                    "model_name": model_name,
                    "field_name": field_name,
                    "reason": "No field_name",
                }
            )
            continue

        if model_name:
            tagged_field = tfm_by_model_field.get((model_name, field_name))

        if not tagged_field and model_name:
            tagged_field = tfm_by_content_field.get((model_name.lower(), field_name))

        if not tagged_field and model_verbose_name:
            tagged_field = tfm_by_verbose_field.get((model_verbose_name, field_name))

        if not tagged_field and field_verbose_name:
            candidates = tfm_by_field_verbose.get((field_name, field_verbose_name), [])
            if len(candidates) == 1:
                tagged_field = candidates[0]

        if not tagged_field:
            candidates = tfm_by_field_only.get(field_name, [])
            if len(candidates) == 1:
                tagged_field = candidates[0]

        if tagged_field:
            updates_to_apply.append((st_id, tagged_field.id))
            updated += 1
        else:
            failed.append(
                {
                    "id": st_id,
                    "model_name": model_name,
                    "field_name": field_name,
                    "reason": "No matching TaggedFieldModel",
                }
            )

    # Apply updates using Django ORM (safe for all database backends)
    if updates_to_apply:
        from django.db import transaction

        with transaction.atomic():
            for st_id, tfm_id in updates_to_apply:
                SystemTag.objects.filter(id=st_id).update(tagged_field_id=tfm_id)

    if failed:
        print(f"\n{'=' * 60}")
        print(
            f"WARNING: Could not find TaggedFieldModel for {len(failed)} SystemTag records:"
        )
        for f in failed[:10]:
            print(
                f"  - SystemTag {f['id']}: {f['model_name']}.{f['field_name']} ({f.get('reason', 'unknown')})"
            )
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
        print("\nThese records may reference models that were renamed or deleted.")
        print("See tag-me documentation for manual repair instructions.")
        print(f"{'=' * 60}\n")

    if updated:
        print(f"Populated tagged_field FK for {updated} SystemTag record(s).")


def reverse_user_tag_fk(apps, schema_editor):
    """Reverse migration - clear UserTag FK fields."""
    UserTag = apps.get_model("tag_me", "UserTag")
    UserTag.objects.update(tagged_field=None)


def reverse_system_tag_fk(apps, schema_editor):
    """Reverse migration - clear SystemTag FK fields."""
    SystemTag = apps.get_model("tag_me", "SystemTag")
    SystemTag.objects.update(tagged_field=None)


def noop(apps, schema_editor):
    """No-op for reverse of check_for_duplicates."""
    pass


class Migration(migrations.Migration):
    """
    Complete the FK-based lookup refactor.

    This migration:
    1. Checks for duplicate (content, field_name) pairs
    2. Adds unique constraint on TaggedFieldModel (content + field_name)
    3. Populates tagged_field FK on existing UserTag/SystemTag records
    4. Updates fields to be nullable with help_text
    5. Adds performance indexes

    NOTE: The tagged_field FK columns already exist from migration 0003.
    """

    dependencies = [
        ("tag_me", "0003_systemtag_comment_systemtag_field_name_and_more"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        # =====================================================================
        # STEP 1: Check for duplicates before adding constraint
        # This prevents cryptic failure and gives helpful guidance
        # =====================================================================
        migrations.RunPython(
            check_for_duplicates,
            noop,
        ),
        # =====================================================================
        # STEP 2: Add unique constraint on TaggedFieldModel
        # This enables reliable FK lookups by content + field_name
        # Using proper Django AddConstraint for correct state tracking
        # =====================================================================
        migrations.AddConstraint(
            model_name="taggedfieldmodel",
            constraint=models.UniqueConstraint(
                fields=["content", "field_name"],
                name="unique_tagged_field_content_field",
            ),
        ),
        # =====================================================================
        # STEP 3: Populate FK fields using resilient matching
        # Uses caching for efficiency on large datasets
        # =====================================================================
        migrations.RunPython(
            populate_user_tag_fk,
            reverse_user_tag_fk,
        ),
        migrations.RunPython(
            populate_system_tag_fk,
            reverse_system_tag_fk,
        ),
        # =====================================================================
        # STEP 4: Update TaggedFieldModel fields to be nullable
        # These fields were originally NOT NULL, need to be nullable for
        # flexibility and consistency
        # =====================================================================
        migrations.AlterField(
            model_name="taggedfieldmodel",
            name="model_name",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                help_text="Cached model name for display. Use content FK for lookups.",
                max_length=255,
                null=True,
                verbose_name="Model name",
            ),
        ),
        migrations.AlterField(
            model_name="taggedfieldmodel",
            name="model_verbose_name",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                max_length=255,
                null=True,
                verbose_name="Model verbose name",
            ),
        ),
        migrations.AlterField(
            model_name="taggedfieldmodel",
            name="field_name",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                max_length=255,
                null=True,
                verbose_name="Field name",
            ),
        ),
        migrations.AlterField(
            model_name="taggedfieldmodel",
            name="field_verbose_name",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                max_length=255,
                null=True,
                verbose_name="Field verbose name",
            ),
        ),
        # =====================================================================
        # STEP 5: Update help_text on UserTag and SystemTag model_name fields
        # =====================================================================
        migrations.AlterField(
            model_name="usertag",
            name="model_name",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                help_text="Cached model name for display. Use tagged_field FK for lookups.",
                max_length=255,
                null=True,
                verbose_name="Model name",
            ),
        ),
        migrations.AlterField(
            model_name="systemtag",
            name="model_name",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                help_text="Cached model name for display. Use tagged_field FK for lookups.",
                max_length=255,
                null=True,
                verbose_name="Model name",
            ),
        ),
        # =====================================================================
        # STEP 6: Update help_text on tagged_field FK fields
        # =====================================================================
        migrations.AlterField(
            model_name="usertag",
            name="tagged_field",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text="FK to TaggedFieldModel. Use this for lookups instead of model_name.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_tags",
                to="tag_me.taggedfieldmodel",
                verbose_name="Tagged Field",
            ),
        ),
        migrations.AlterField(
            model_name="systemtag",
            name="tagged_field",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text="FK to TaggedFieldModel. Use this for lookups instead of model_name.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="system_tags",
                to="tag_me.taggedfieldmodel",
                verbose_name="Tagged Field",
            ),
        ),
        # =====================================================================
        # STEP 7: Add indexes for query performance
        # Using proper Django AddIndex for correct state tracking
        # =====================================================================
        migrations.AddIndex(
            model_name="usertag",
            index=models.Index(
                fields=["tagged_field", "user"],
                name="tag_me_user_tagged_user_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="systemtag",
            index=models.Index(
                fields=["tagged_field"],
                name="tag_me_sys_tagged_field_idx",
            ),
        ),
    ]
