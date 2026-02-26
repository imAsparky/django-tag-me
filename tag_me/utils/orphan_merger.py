"""
tag_me/utils/orphan_merger.py

Automatic detection and merging of orphaned TaggedFieldModel records.

Root Cause:
    When a user renames a Django model, Django may generate DeleteModel + CreateModel
    instead of RenameModel. This creates a NEW ContentType (and thus new TaggedFieldModel
    records) while the OLD ContentType becomes stale (model_class() returns None).

    Even with RenameModel, Django's ContentType cache can cause duplicate ContentTypes
    to be created if the cache isn't cleared before get_for_model() is called.

    The old TaggedFieldModel records still have UserTag/SystemTag FKs pointing to them,
    but the new records don't. This results in:
    - Users losing their tag associations
    - Orphaned records accumulating in the database

Solution:
    After every field registration (post-migrate), scan for orphaned TaggedFieldModel
    records and merge them into the new records automatically.

Matching Strategy (in order of priority):
    1. UNIQUE MATCH: Same app_label + field_name + tag_type with exactly one valid candidate
    2. FIELD SIGNATURE: When multiple candidates exist, compare the full set of field_names
       for the orphan's ContentType against each candidate's ContentType. The candidate
       whose field set matches is the renamed model.
"""

from collections import defaultdict

import structlog
from django.db import transaction

logger = structlog.get_logger(__name__)


def merge_orphaned_tagged_fields():
    """
    Detect and merge orphaned TaggedFieldModel records.

    This function should be called after save_fields() completes during
    post-migrate, so that new TaggedFieldModel records already exist
    as merge targets.

    Returns:
        dict: Summary with keys 'merged', 'unresolved', 'details'
    """
    # Late imports to avoid circular imports and ensure apps are ready
    from tag_me.models import TaggedFieldModel

    result = {"merged": 0, "unresolved": 0, "details": []}

    # Step 1: Find all orphaned TaggedFieldModel records
    # (ContentType exists but model_class() is None — model was deleted/renamed)
    orphaned = []
    for tfm in TaggedFieldModel.objects.select_related("content").all():
        if tfm.content is None:
            orphaned.append(tfm)
        elif tfm.content.model_class() is None:
            orphaned.append(tfm)

    if not orphaned:
        return result

    logger.info(
        "orphan_scan_found",
        orphan_count=len(orphaned),
    )

    # Step 2: Build field signature map — for each content_id, what field_names exist?
    # This is used to resolve ambiguous matches (e.g., "emotions" exists in 3 models)
    field_signatures = _build_field_signatures(TaggedFieldModel)

    # Step 3: Group orphans by content_id for batch processing
    orphans_by_content = defaultdict(list)
    for tfm in orphaned:
        ct_id = tfm.content_id if tfm.content else None
        orphans_by_content[ct_id].append(tfm)

    stale_content_types = set()

    for content_id, orphan_group in orphans_by_content.items():
        if content_id is None:
            for old_tfm in orphan_group:
                _record_unresolved(result, old_tfm, "no ContentType FK")
            continue

        # Get the orphan's field signature (all field_names under this content_id)
        orphan_signature = field_signatures.get(content_id, set())
        old_ct = orphan_group[0].content
        app_label = old_ct.app_label if old_ct else None

        if not app_label:
            for old_tfm in orphan_group:
                _record_unresolved(result, old_tfm, "no app_label")
            continue

        for old_tfm in orphan_group:
            if not old_tfm.field_name:
                _record_unresolved(result, old_tfm, "no field_name")
                continue

            # Find candidates: same app + same field_name + same tag_type + valid model
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

            # Strategy 1: Unambiguous — only one candidate
            if len(valid_candidates) == 1:
                new_tfm = valid_candidates[0]
                _merge_tagged_field(old_tfm, new_tfm)
                result["merged"] += 1

                if old_ct:
                    stale_content_types.add(old_ct)

                logger.info(
                    "orphan_merged",
                    old_model=old_tfm.model_name,
                    new_model=new_tfm.model_name,
                    field_name=old_tfm.field_name,
                    old_tfm_id=old_tfm.id,
                    new_tfm_id=new_tfm.id,
                    resolution="unique_match",
                )

            # Strategy 2: Ambiguous — use field signature to disambiguate
            elif len(valid_candidates) > 1:
                new_tfm = _resolve_by_field_signature(
                    old_tfm, valid_candidates, orphan_signature, field_signatures
                )

                if new_tfm:
                    _merge_tagged_field(old_tfm, new_tfm)
                    result["merged"] += 1

                    if old_ct:
                        stale_content_types.add(old_ct)

                    logger.info(
                        "orphan_merged",
                        old_model=old_tfm.model_name,
                        new_model=new_tfm.model_name,
                        field_name=old_tfm.field_name,
                        old_tfm_id=old_tfm.id,
                        new_tfm_id=new_tfm.id,
                        resolution="field_signature",
                    )
                else:
                    candidate_names = [
                        f"{c.model_name}.{c.field_name}" for c in valid_candidates
                    ]
                    logger.warning(
                        "orphan_unresolved",
                        orphan_id=old_tfm.id,
                        model_name=old_tfm.model_name,
                        field_name=old_tfm.field_name,
                        reason="ambiguous",
                        candidate_count=len(valid_candidates),
                        candidates=candidate_names,
                    )
                    _record_unresolved(
                        result,
                        old_tfm,
                        f"ambiguous — {len(valid_candidates)} candidates, "
                        f"field signature did not resolve",
                    )

            else:
                logger.warning(
                    "orphan_unresolved",
                    orphan_id=old_tfm.id,
                    model_name=old_tfm.model_name,
                    field_name=old_tfm.field_name,
                    reason="no_matching_target",
                )
                _record_unresolved(result, old_tfm, "no matching target found")

    # Step 4: Clean up stale ContentTypes with no remaining references
    for stale_ct in stale_content_types:
        remaining = TaggedFieldModel.objects.filter(content=stale_ct).count()
        if remaining == 0:
            logger.info(
                "stale_content_type_deleted",
                content_type_id=stale_ct.id,
                app_label=stale_ct.app_label,
                model=stale_ct.model,
            )
            stale_ct.delete()

    if result["merged"] or result["unresolved"]:
        logger.info(
            "orphan_merge_completed",
            merged=result["merged"],
            unresolved=result["unresolved"],
        )

    return result


def _build_field_signatures(TaggedFieldModel):
    """
    Build a mapping of content_id → set of field_names.

    This "field signature" represents the shape of a model's tagged fields.
    When a model is renamed, its field signature stays the same, so we can
    use it to match orphaned records to their replacement.

    Returns:
        dict: {content_id: set of field_name strings}
    """
    signatures = defaultdict(set)
    for content_id, field_name in TaggedFieldModel.objects.values_list(
        "content_id", "field_name"
    ):
        if field_name:
            signatures[content_id].add(field_name)
    return dict(signatures)


def _resolve_by_field_signature(
    old_tfm, candidates, orphan_signature, field_signatures
):
    """
    Resolve an ambiguous match using field signatures.

    Compares the orphan's full set of field_names against each candidate's
    content_id's field set. The candidate whose model has the same field
    signature as the orphan is the renamed model.

    For example, if the orphan's ContentType has fields {emotions, other}
    and candidate A's ContentType has {emotions, other, adjustments} while
    candidate B has {emotions, other}, then B is the match.

    Falls back to Jaccard similarity if no exact match is found, requiring
    both a minimum threshold and a clear winner.

    Args:
        old_tfm: The orphaned TaggedFieldModel
        candidates: List of valid candidate TaggedFieldModels
        orphan_signature: Set of field_names for the orphan's content_id
        field_signatures: Dict mapping content_id → set of field_names

    Returns:
        TaggedFieldModel or None: The matched candidate, or None if still ambiguous
    """
    if not orphan_signature:
        return None

    # Strategy 2a: Exact signature match
    matching_candidates = []
    for candidate in candidates:
        candidate_signature = field_signatures.get(candidate.content_id, set())
        if candidate_signature == orphan_signature:
            matching_candidates.append(candidate)

    if len(matching_candidates) == 1:
        return matching_candidates[0]

    # Strategy 2b: Jaccard similarity — for cases where fields were added/removed
    # alongside the rename. Require ≥50% overlap AND a clear winner.
    best_candidate = None
    best_score = 0
    runner_up_score = 0

    for candidate in candidates:
        candidate_signature = field_signatures.get(candidate.content_id, set())
        intersection = len(orphan_signature & candidate_signature)
        union = len(orphan_signature | candidate_signature)

        if union == 0:
            continue

        score = intersection / union

        if score > best_score:
            runner_up_score = best_score
            best_score = score
            best_candidate = candidate
        elif score > runner_up_score:
            runner_up_score = score

    # Require: ≥50% Jaccard AND winner is clearly ahead of runner-up
    if best_candidate and best_score >= 0.5 and best_score > runner_up_score:
        return best_candidate

    return None


def _record_unresolved(result, tfm, reason):
    """Record an unresolved orphan in the result dict."""
    result["unresolved"] += 1
    result["details"].append(
        {
            "id": tfm.id,
            "model_name": tfm.model_name,
            "field_name": tfm.field_name,
            "reason": reason,
        }
    )


def _merge_tagged_field(old_tfm, new_tfm):
    """
    Merge an orphaned TaggedFieldModel into its replacement.

    Migrates all UserTag and SystemTag FK references from old → new,
    handling potential unique constraint conflicts, then deletes the
    orphaned record.

    Args:
        old_tfm: The orphaned TaggedFieldModel (model was deleted/renamed)
        new_tfm: The replacement TaggedFieldModel (new model name)
    """
    from tag_me.models import SystemTag, UserTag

    with transaction.atomic():
        # --- Migrate UserTags ---
        ut_migrated = 0
        ut_merged = 0

        for old_ut in old_tfm.user_tags.all():
            existing = UserTag.objects.filter(
                user=old_ut.user,
                tagged_field=new_tfm,
            ).first()

            if existing:
                if old_ut.tags and old_ut.tags.strip():
                    _merge_tag_strings(source=old_ut, target=existing)
                    existing.save()
                old_ut.delete()
                ut_merged += 1
            else:
                old_ut.tagged_field = new_tfm
                old_ut.model_name = new_tfm.model_name
                old_ut.model_verbose_name = new_tfm.model_verbose_name
                old_ut.save()
                ut_migrated += 1

        # --- Migrate SystemTags ---
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

        # Delete the orphaned TaggedFieldModel
        old_tfm.delete()

    logger.debug(
        "orphan_merge_detail",
        old_tfm_id=old_tfm.id,
        new_tfm_id=new_tfm.id,
        user_tags_migrated=ut_migrated,
        user_tags_merged=ut_merged,
        system_tags_migrated=st_migrated,
        system_tags_merged=st_merged,
    )


def _merge_tag_strings(source, target):
    """
    Merge tags from source into target, avoiding duplicates.

    Both source.tags and target.tags are comma-separated strings.
    The merged result preserves existing tags and adds any new ones.

    Args:
        source: Tag record with tags to merge FROM
        target: Tag record with tags to merge INTO (modified in place)
    """
    from tag_me.utils.parser import parse_tags

    source_tags = set(parse_tags(source.tags)) if source.tags else set()
    target_tags = set(parse_tags(target.tags)) if target.tags else set()

    merged = target_tags | source_tags

    if merged != target_tags:
        target.tags = ",".join(sorted(merged))

    # Also merge search_tags if present
    if hasattr(source, "search_tags") and hasattr(target, "search_tags"):
        source_search = (
            set(parse_tags(source.search_tags)) if source.search_tags else set()
        )
        target_search = (
            set(parse_tags(target.search_tags)) if target.search_tags else set()
        )
        merged_search = target_search | source_search
        if merged_search != target_search:
            target.search_tags = ",".join(sorted(merged_search))
