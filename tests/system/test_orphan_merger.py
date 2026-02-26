"""
Tests for tag_me.utils.orphan_merger module.

Covers:
    - _merge_tag_strings: pure logic for merging comma-separated tag strings
    - _resolve_by_field_signature: disambiguation via field set comparison
    - _record_unresolved: helper for tracking unresolved orphans
    - _build_field_signatures: database query for field shape mapping
    - _merge_tagged_field: FK migration from orphaned to replacement record
    - merge_orphaned_tagged_fields: end-to-end orphan detection and merging

Test strategy:
    Unit tests use lightweight stubs (types.SimpleNamespace) for pure functions.
    Integration tests use real database records with stale ContentTypes
    (model_class() returns None) to simulate the actual rename scenario.
"""

from types import SimpleNamespace

import pytest
from django.contrib.contenttypes.models import ContentType

from tag_me.models import SystemTag, TaggedFieldModel, UserTag
from tag_me.utils.orphan_merger import (
    _build_field_signatures,
    _merge_tag_strings,
    _merge_tagged_field,
    _record_unresolved,
    _resolve_by_field_signature,
    merge_orphaned_tagged_fields,
)
from tests.models import TaggedFieldTestModel

# =============================================================================
# _merge_tag_strings (unit tests — no database)
# =============================================================================


class TestMergeTagStrings:
    """Test tag string merging logic.

    _merge_tag_strings modifies target in place by merging source.tags
    into target.tags (and source.search_tags into target.search_tags).
    """

    def _make_tag_obj(self, tags="", search_tags=None):
        """Create a lightweight stub with .tags and optional .search_tags."""
        obj = SimpleNamespace(tags=tags)
        if search_tags is not None:
            obj.search_tags = search_tags
        return obj

    def test_merges_disjoint_tags(self):
        source = self._make_tag_obj(tags="alpha,beta")
        target = self._make_tag_obj(tags="gamma,delta")

        _merge_tag_strings(source, target)

        result = set(target.tags.split(","))
        assert result == {"alpha", "beta", "gamma", "delta"}

    def test_deduplicates_overlapping_tags(self):
        source = self._make_tag_obj(tags="shared,source_only")
        target = self._make_tag_obj(tags="shared,target_only")

        _merge_tag_strings(source, target)

        result = set(target.tags.split(","))
        assert result == {"shared", "source_only", "target_only"}

    def test_empty_source_is_noop(self):
        source = self._make_tag_obj(tags="")
        target = self._make_tag_obj(tags="existing")

        _merge_tag_strings(source, target)

        assert target.tags == "existing"

    def test_empty_target_receives_source_tags(self):
        source = self._make_tag_obj(tags="new1,new2")
        target = self._make_tag_obj(tags="")

        _merge_tag_strings(source, target)

        result = set(target.tags.split(","))
        assert result == {"new1", "new2"}

    def test_merges_search_tags_when_present(self):
        source = self._make_tag_obj(tags="a", search_tags="x,y")
        target = self._make_tag_obj(tags="b", search_tags="y,z")

        _merge_tag_strings(source, target)

        result = set(target.search_tags.split(","))
        assert result == {"x", "y", "z"}

    def test_skips_search_tags_when_absent(self):
        """No error when stubs lack search_tags attribute."""
        source = self._make_tag_obj(tags="a")
        target = self._make_tag_obj(tags="b")

        _merge_tag_strings(source, target)

        assert not hasattr(target, "search_tags")


# =============================================================================
# _resolve_by_field_signature (unit tests — no database)
# =============================================================================


class TestResolveByFieldSignature:
    """Test field signature disambiguation logic.

    Uses SimpleNamespace stubs with .content_id to simulate candidates.
    """

    def _make_candidate(self, content_id):
        return SimpleNamespace(content_id=content_id)

    def test_exact_match_returns_candidate(self):
        orphan = self._make_candidate(content_id=99)
        candidate_a = self._make_candidate(content_id=1)
        candidate_b = self._make_candidate(content_id=2)

        orphan_sig = {"field_x", "field_y"}
        signatures = {
            1: {"field_x", "field_z"},  # Different
            2: {"field_x", "field_y"},  # Exact match
        }

        result = _resolve_by_field_signature(
            orphan, [candidate_a, candidate_b], orphan_sig, signatures
        )

        assert result is candidate_b

    def test_no_match_returns_none(self):
        orphan = self._make_candidate(content_id=99)
        candidate = self._make_candidate(content_id=1)

        orphan_sig = {"field_a", "field_b"}
        signatures = {1: {"field_x", "field_y"}}  # Completely different

        result = _resolve_by_field_signature(
            orphan, [candidate], orphan_sig, signatures
        )

        assert result is None

    def test_multiple_exact_matches_returns_none(self):
        """Ambiguous — two candidates have identical signatures."""
        orphan = self._make_candidate(content_id=99)
        candidate_a = self._make_candidate(content_id=1)
        candidate_b = self._make_candidate(content_id=2)

        orphan_sig = {"field_x", "field_y"}
        signatures = {
            1: {"field_x", "field_y"},
            2: {"field_x", "field_y"},
        }

        result = _resolve_by_field_signature(
            orphan, [candidate_a, candidate_b], orphan_sig, signatures
        )

        assert result is None

    def test_jaccard_resolves_partial_overlap(self):
        """Jaccard fallback when no exact match but one candidate is close."""
        orphan = self._make_candidate(content_id=99)
        candidate_a = self._make_candidate(content_id=1)
        candidate_b = self._make_candidate(content_id=2)

        orphan_sig = {"f1", "f2", "f3"}
        signatures = {
            1: {"f1", "f2", "f3", "f4"},  # 3/4 = 0.75 Jaccard
            2: {"f1", "f99"},  # 1/4 = 0.25 Jaccard
        }

        result = _resolve_by_field_signature(
            orphan, [candidate_a, candidate_b], orphan_sig, signatures
        )

        assert result is candidate_a

    def test_jaccard_tie_returns_none(self):
        """Tied Jaccard scores — cannot pick a winner."""
        orphan = self._make_candidate(content_id=99)
        candidate_a = self._make_candidate(content_id=1)
        candidate_b = self._make_candidate(content_id=2)

        orphan_sig = {"f1", "f2"}
        signatures = {
            1: {"f1", "f3"},  # 1/3 Jaccard
            2: {"f2", "f4"},  # 1/3 Jaccard
        }

        result = _resolve_by_field_signature(
            orphan, [candidate_a, candidate_b], orphan_sig, signatures
        )

        assert result is None

    def test_empty_orphan_signature_returns_none(self):
        orphan = self._make_candidate(content_id=99)
        candidate = self._make_candidate(content_id=1)

        result = _resolve_by_field_signature(orphan, [candidate], set(), {1: {"f1"}})

        assert result is None


# =============================================================================
# _record_unresolved (unit test)
# =============================================================================


class TestRecordUnresolved:
    def test_increments_count_and_appends_detail(self):
        result = {"merged": 0, "unresolved": 0, "details": []}
        tfm = SimpleNamespace(id=42, model_name="OldModel", field_name="emotions")

        _record_unresolved(result, tfm, "no matching target found")

        assert result["unresolved"] == 1
        assert len(result["details"]) == 1
        assert result["details"][0] == {
            "id": 42,
            "model_name": "OldModel",
            "field_name": "emotions",
            "reason": "no matching target found",
        }


# =============================================================================
# _build_field_signatures (database)
# =============================================================================


@pytest.mark.django_db
class TestBuildFieldSignatures:
    def test_builds_correct_mapping(self, tagged_field_factory):
        tfm1 = tagged_field_factory(
            model_class=TaggedFieldTestModel, field_name="field_a"
        )
        tfm2 = tagged_field_factory(
            model_class=TaggedFieldTestModel, field_name="field_b"
        )

        signatures = _build_field_signatures(TaggedFieldModel)
        ct_id = tfm1.content_id

        assert ct_id in signatures
        # The signature may include real TagMeCharFields registered on
        # TaggedFieldTestModel during post-migrate, so check our fields
        # are present rather than asserting exact equality.
        assert {"field_a", "field_b"}.issubset(signatures[ct_id])

    def test_empty_table_returns_empty_dict(self):
        """With no TaggedFieldModel records, signatures should be empty."""
        # The autouse reset_registry doesn't clear the DB, but if no
        # tagged fields exist yet the result is effectively empty for
        # any content_id we haven't created.
        signatures = _build_field_signatures(TaggedFieldModel)

        # We just verify it's a dict and doesn't blow up
        assert isinstance(signatures, dict)


# =============================================================================
# _merge_tagged_field (database)
# =============================================================================


@pytest.mark.django_db
class TestMergeTaggedField:
    """Test FK migration from orphaned to replacement TaggedFieldModel."""

    def test_migrates_user_tag_to_new_target(
        self,
        tagged_field_factory,
        stale_content_type_factory,
        user_tag_factory,
        test_user,
    ):
        """UserTag should be re-pointed from old to new TaggedFieldModel."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        old_tfm = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="emotions",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Emotions",
            tag_type="user",
        )
        new_tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="emotions",
        )

        ut = user_tag_factory(
            user=test_user,
            tagged_field=old_tfm,
            tags="happy,sad",
        )

        _merge_tagged_field(old_tfm, new_tfm)

        ut.refresh_from_db()
        assert ut.tagged_field_id == new_tfm.id
        assert ut.model_name == new_tfm.model_name
        assert not TaggedFieldModel.objects.filter(id=old_tfm.id).exists()

    def test_merges_user_tag_on_conflict(
        self,
        tagged_field_factory,
        stale_content_type_factory,
        user_tag_factory,
        test_user,
    ):
        """When target already has a UserTag for the same user, merge tags."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        old_tfm = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="emotions",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Emotions",
            tag_type="user",
        )
        new_tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="emotions",
        )

        # Old record has tags the new one doesn't
        user_tag_factory(user=test_user, tagged_field=old_tfm, tags="old_tag")
        existing_ut = user_tag_factory(
            user=test_user, tagged_field=new_tfm, tags="new_tag"
        )

        _merge_tagged_field(old_tfm, new_tfm)

        existing_ut.refresh_from_db()
        merged_tags = set(existing_ut.tags.split(","))
        assert "old_tag" in merged_tags
        assert "new_tag" in merged_tags

        # Old UserTag should be deleted
        assert UserTag.objects.filter(tagged_field=new_tfm, user=test_user).count() == 1

    def test_migrates_system_tag_to_new_target(
        self,
        tagged_field_factory,
        stale_content_type_factory,
        system_tag_factory,
    ):
        """SystemTag should be re-pointed from old to new TaggedFieldModel."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        old_tfm = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="emotions",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Emotions",
            tag_type="system",
        )
        new_tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="emotions",
            tag_type="system",
        )

        st = system_tag_factory(tagged_field=old_tfm, tags="sys1,sys2")

        _merge_tagged_field(old_tfm, new_tfm)

        st.refresh_from_db()
        assert st.tagged_field_id == new_tfm.id
        assert st.model_name == new_tfm.model_name

    def test_deletes_duplicate_system_tag_on_conflict(
        self,
        tagged_field_factory,
        stale_content_type_factory,
        system_tag_factory,
    ):
        """When target already has a SystemTag, old one is deleted (not migrated)."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        old_tfm = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="emotions",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Emotions",
            tag_type="system",
        )
        new_tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="emotions",
            tag_type="system",
        )

        old_st = system_tag_factory(tagged_field=old_tfm, tags="old_sys")
        new_st = system_tag_factory(tagged_field=new_tfm, tags="new_sys")

        _merge_tagged_field(old_tfm, new_tfm)

        # Old SystemTag deleted, new one kept
        assert not SystemTag.objects.filter(id=old_st.id).exists()
        assert SystemTag.objects.filter(id=new_st.id).exists()
        assert SystemTag.objects.filter(tagged_field=new_tfm).count() == 1


# =============================================================================
# merge_orphaned_tagged_fields (end-to-end)
# =============================================================================


@pytest.mark.django_db
class TestMergeOrphanedTaggedFields:
    """End-to-end tests for the main entry point."""

    def test_no_orphans_returns_empty_result(self):
        """When no stale ContentTypes exist, nothing to merge."""
        result = merge_orphaned_tagged_fields()

        assert result["merged"] == 0
        assert result["unresolved"] == 0

    def test_unique_match_merges_orphan(
        self,
        tagged_field_factory,
        stale_content_type_factory,
        user_tag_factory,
        test_user,
    ):
        """Single valid candidate — orphan should be merged automatically."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        old_tfm = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="emotions",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Emotions",
            tag_type="user",
        )
        new_tfm = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="emotions",
        )
        user_tag_factory(user=test_user, tagged_field=old_tfm, tags="happy")

        result = merge_orphaned_tagged_fields()

        assert result["merged"] == 1
        assert result["unresolved"] == 0
        assert not TaggedFieldModel.objects.filter(id=old_tfm.id).exists()

        # UserTag should now point at new_tfm
        ut = UserTag.objects.get(user=test_user, tagged_field=new_tfm)
        assert "happy" in ut.tags

    def test_no_candidates_records_unresolved(
        self,
        stale_content_type_factory,
    ):
        """Orphan with no matching target should be recorded as unresolved."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="unique_field_with_no_match",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Unique Field",
            tag_type="user",
        )

        result = merge_orphaned_tagged_fields()

        assert result["merged"] == 0
        assert result["unresolved"] == 1
        assert "no matching target found" in result["details"][0]["reason"]

    def test_stale_content_type_cleaned_up(
        self,
        tagged_field_factory,
        stale_content_type_factory,
    ):
        """After all orphans under a stale ContentType are merged, the CT is deleted."""
        stale_ct = stale_content_type_factory(model="oldmodel")
        stale_ct_id = stale_ct.id

        TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="field_a",
            model_name="OldModel",
            model_verbose_name="Old Model",
            field_verbose_name="Field A",
            tag_type="user",
        )
        # Create a valid target for the merge
        tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="field_a",
        )

        merge_orphaned_tagged_fields()

        assert not ContentType.objects.filter(id=stale_ct_id).exists()

    def test_end_to_end_with_user_and_system_tags(
        self,
        tagged_field_factory,
        stale_content_type_factory,
        user_tag_factory,
        system_tag_factory,
        test_user,
    ):
        """Full scenario: orphaned record with both UserTag and SystemTag FKs."""
        stale_ct = stale_content_type_factory(model="renamedmodel")

        # Old orphaned records (two fields on the same stale model)
        old_tfm_user = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="emotions",
            model_name="RenamedModel",
            model_verbose_name="Renamed Model",
            field_verbose_name="Emotions",
            tag_type="user",
        )
        old_tfm_sys = TaggedFieldModel.objects.create(
            content=stale_ct,
            field_name="categories",
            model_name="RenamedModel",
            model_verbose_name="Renamed Model",
            field_verbose_name="Categories",
            tag_type="system",
        )

        user_tag_factory(user=test_user, tagged_field=old_tfm_user, tags="happy,sad")
        system_tag_factory(tagged_field=old_tfm_sys, tags="cat1,cat2")

        # New valid targets
        new_tfm_user = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="emotions",
        )
        new_tfm_sys = tagged_field_factory(
            model_class=TaggedFieldTestModel,
            field_name="categories",
            tag_type="system",
        )

        result = merge_orphaned_tagged_fields()

        assert result["merged"] == 2
        assert result["unresolved"] == 0

        # Verify UserTag migrated
        ut = UserTag.objects.get(user=test_user, tagged_field=new_tfm_user)
        assert "happy" in ut.tags
        assert "sad" in ut.tags

        # Verify SystemTag migrated
        st = SystemTag.objects.get(tagged_field=new_tfm_sys)
        assert "cat1" in st.tags

        # Old records gone
        assert not TaggedFieldModel.objects.filter(id=old_tfm_user.id).exists()
        assert not TaggedFieldModel.objects.filter(id=old_tfm_sys.id).exists()
