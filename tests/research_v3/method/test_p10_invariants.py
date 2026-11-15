"""P10 invariant tests: cycle rejection, grade inversion, Bloom leaps, anchors.

Spec source: LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115/05_PAPERS/P10_*.md
packet §5 falsification counters + the user instruction: "Tests: cycle
rejected; grade inversion rejected; Bloom depth leap flagged; missing anchor
rejected; determinism; negative case with an invented competency code must be
flagged needs_expert_review (not silently accepted)."
"""
from __future__ import annotations

import pytest

from tests.research_v3.method.conftest import make_object
from research_v3.methods.p10.anchors import (
    CurriculumAnchor,
    LearningObject,
    P10ContractError,
    PrerequisiteEdge,
)
from research_v3.methods.p10.registry import (
    build_anchor_registry,
    anchor_confidence_summary,
    assert_anchor_known,
)
from research_v3.methods.p10.spiral_builder import (
    BloomAscentError,
    CycleError,
    GradeInversionError,
    UnknownAnchorError,
    build_certificate,
    build_spiral_dag,
    check_anchors,
    check_acyclic,
    check_bloom_ascent,
    check_grade_monotone,
)


# ---------------------------------------------------------------------------
# I-ACYCLIC: cycle rejected
# ---------------------------------------------------------------------------
class TestCycleRejection:
    def test_direct_two_node_cycle_rejected(self):
        a = make_object("obj_a", grade=10, layer=1)
        b = make_object("obj_b", grade=11, layer=2)
        objects = {o.object_id: o for o in (a, b)}
        edges = [
            PrerequisiteEdge("obj_a", "obj_b"),
            PrerequisiteEdge("obj_b", "obj_a"),
        ]
        with pytest.raises(CycleError):
            check_acyclic(objects, edges)

    def test_three_node_cycle_rejected_with_path_in_message(self):
        a = make_object("obj_a")
        b = make_object("obj_b")
        c = make_object("obj_c")
        objects = {o.object_id: o for o in (a, b, c)}
        edges = [
            PrerequisiteEdge("obj_a", "obj_b"),
            PrerequisiteEdge("obj_b", "obj_c"),
            PrerequisiteEdge("obj_c", "obj_a"),
        ]
        with pytest.raises(CycleError, match="obj_a"):
            check_acyclic(objects, edges)

    def test_diamond_dag_is_not_a_cycle(self):
        a = make_object("obj_a", grade=10, layer=1)
        b = make_object("obj_b", grade=10, layer=1, category="dong_vat")
        c = make_object("obj_c", grade=11, layer=2, category="kien_truc")
        d = make_object("obj_d", grade=12, layer=3, category="dia_ly")
        objects = {o.object_id: o for o in (a, b, c, d)}
        edges = [
            PrerequisiteEdge("obj_a", "obj_c"),
            PrerequisiteEdge("obj_b", "obj_c"),
            PrerequisiteEdge("obj_c", "obj_d"),
        ]
        check_acyclic(objects, edges)  # must not raise

    def test_certificate_reports_cycle_instead_of_building(self, anchor_registry):
        a = make_object("obj_a")
        b = make_object("obj_b")
        objects = {o.object_id: o for o in (a, b)}
        edges = [PrerequisiteEdge("obj_a", "obj_b"), PrerequisiteEdge("obj_b", "obj_a")]
        cert = build_certificate([], objects, edges, anchor_registry)
        assert not cert.acyclic
        assert not cert.valid
        assert any("prerequisite_cycle_detected" in rc for rc in cert.reason_codes)

    def test_self_loop_is_never_constructible(self):
        with pytest.raises(P10ContractError):
            PrerequisiteEdge("obj_a", "obj_a")


# ---------------------------------------------------------------------------
# I-GRADE-MONOTONE: grade inversion rejected
# ---------------------------------------------------------------------------
class TestGradeInversion:
    def test_grade_inverting_edge_rejected(self):
        g10 = make_object("obj_g10", grade=10, layer=1)
        g12 = make_object("obj_g12", grade=12, layer=3, category="dia_ly")
        objects = {o.object_id: o for o in (g10, g12)}
        edges = [PrerequisiteEdge("obj_g12", "obj_g10")]  # 12 -> 10 inversion
        with pytest.raises(GradeInversionError):
            check_grade_monotone(objects, edges)

    def test_equal_grade_edge_allowed(self):
        a = make_object("obj_a", grade=10, layer=1, category="linh_thu")
        b = make_object("obj_b", grade=10, layer=1, category="dong_vat")
        objects = {o.object_id: o for o in (a, b)}
        check_grade_monotone(objects, [PrerequisiteEdge("obj_a", "obj_b")])

    def test_out_of_scope_grade_rejected_at_construction(self):
        with pytest.raises(P10ContractError, match="grade"):
            make_object("obj_g9", grade=9, layer=1)

    def test_inversion_reported_in_certificate(self, anchor_registry):
        g10 = make_object("obj_g10", grade=10, layer=1)
        g12 = make_object("obj_g12", grade=12, layer=3, category="dia_ly")
        objects = {o.object_id: o for o in (g10, g12)}
        edges = [PrerequisiteEdge("obj_g12", "obj_g10")]
        cert = build_certificate([], objects, edges, anchor_registry)
        assert not cert.grade_monotone
        assert not cert.valid


# ---------------------------------------------------------------------------
# I-BLOOM-ASCENT: flat rejected; leaps flagged (not silently accepted)
# ---------------------------------------------------------------------------
class TestBloomGating:
    def test_flat_bloom_edge_rejected_when_min_ascent_positive(self):
        a = make_object("obj_a", grade=10, layer=1, bloom=2)
        b = make_object("obj_b", grade=10, layer=1, bloom=2, category="dong_vat")
        objects = {o.object_id: o for o in (a, b)}
        edges = [PrerequisiteEdge("obj_a", "obj_b")]
        with pytest.raises(BloomAscentError):
            check_bloom_ascent(objects, edges, min_ascent=1)

    def test_bloom_leap_is_flagged_not_rejected(self):
        """A 3-level jump must appear in bloom_leap_edges (expert warning)."""
        a = make_object("obj_a", grade=10, layer=1, bloom=1)
        b = make_object("obj_b", grade=12, layer=3, bloom=5, category="dia_ly")
        objects = {o.object_id: o for o in (a, b)}
        edges = [PrerequisiteEdge("obj_a", "obj_b")]
        leaps = check_bloom_ascent(objects, edges, min_ascent=0, max_leap=2)
        assert leaps == ("obj_a->obj_b:+4",)

    def test_bloom_leap_within_layer_band_is_a_contract_violation(self):
        """Objects cannot silently carry Bloom levels outside their layer band."""
        with pytest.raises(P10ContractError, match="band"):
            LearningObject(
                object_id="obj_bad",
                urn_slug="cao-dinh",
                motif_name_vi="x",
                category="linh_thu",
                grade=10,
                layer=1,
                bloom_level=5,  # layer 1 band is 1..2
                anchor_code="LS10-CHUYENDE-BAO_TON_DI_SAN",
            )

    def test_leap_flagged_in_certificate_but_validity_preserved(self, anchor_registry):
        a = make_object("obj_a", grade=10, layer=1, bloom=1)
        b = make_object(
            "obj_b", grade=12, layer=3, bloom=5, category="dia_ly",
            anchor="P10-LOCAL-dia_ly-G12",
        )
        objects = {o.object_id: o for o in (a, b)}
        edges = [PrerequisiteEdge("obj_a", "obj_b")]
        cert = build_certificate([], objects, edges, anchor_registry, max_leap=2)
        assert cert.valid  # leap flags, does not reject
        assert cert.bloom_leap_edges == ("obj_a->obj_b:+4",)
        assert any("bloom_leap_flagged" in rc for rc in cert.reason_codes)


# ---------------------------------------------------------------------------
# I-ANCHOR: missing/unknown anchor rejected; grade mismatch rejected
# ---------------------------------------------------------------------------
class TestAnchorGate:
    def test_unknown_anchor_raises_not_silently_passes(self, anchor_registry):
        obj = make_object("obj_inv", anchor="NH10-FABRICATED-COMPETENCY")
        objects = {obj.object_id: obj}
        with pytest.raises(UnknownAnchorError):
            check_anchors(objects, anchor_registry)

    def test_missing_anchor_code_rejected_at_construction(self):
        with pytest.raises(P10ContractError, match="anchor"):
            LearningObject(
                object_id="obj_no_anchor",
                urn_slug="cao-dinh",
                motif_name_vi="x",
                category="linh_thu",
                grade=10,
                layer=1,
                bloom_level=2,
                anchor_code="",
            )

    def test_anchor_grade_mismatch_rejected(self, anchor_registry):
        # dia_ly anchors exist only as P10-LOCAL-*-G12, grade 12
        obj = make_object(
            "obj_misplaced",
            grade=10,
            layer=1,
            category="dia_ly",
            anchor="P10-LOCAL-dia_ly-G12",
        )
        objects = {obj.object_id: obj}
        with pytest.raises(P10ContractError, match="serves grade"):
            check_anchors(objects, anchor_registry)

    def test_certificate_reports_unknown_anchor(self, anchor_registry):
        obj = make_object("obj_inv", anchor="TOTALLY-MADE-UP-2026")
        objects = {obj.object_id: obj}
        cert = build_certificate([], objects, [], anchor_registry)
        assert not cert.anchors_resolved
        assert not cert.valid
        assert any("unknown_curriculum_anchor" in rc for rc in cert.reason_codes)


# ---------------------------------------------------------------------------
# Fabrication guard: invented competency code -> needs_expert_review, never documented
# ---------------------------------------------------------------------------
class TestInventedCompetencyCode:
    def test_invented_code_is_never_classified_documented(self, anchor_registry):
        """The negative case from the task list: an invented competency code
        must be flagged needs_expert_review — never silently accepted as
        documented. The registry itself contains zero fabricated codes: every
        non-ministerial anchor is explicitly P10-LOCAL-* with
        confidence_status=needs_expert_review."""
        registry = build_anchor_registry()
        for code, anchor in registry.items():
            if code.startswith("P10-LOCAL-"):
                assert anchor.confidence_status == "needs_expert_review", code
            # No anchor may carry a fabricated official-looking numeraire.
            if not code.startswith("P10-LOCAL-"):
                assert anchor.source_citation.strip(), code

    def test_invented_code_through_registry_gate_raises(self):
        from research_v3.methods.p10.anchors import UnknownAnchorError

        with pytest.raises(UnknownAnchorError, match="INVENTED"):
            assert_anchor_known(build_anchor_registry(), "NH10.2.3-INVENTED")

    def test_review_anchored_object_builds_only_when_marked_pending(self, anchor_registry):
        """A teacher-pending mapping CAN be used — but only via its honest
        P10-LOCAL code, and its status propagates as needs_expert_review."""
        obj = make_object(
            "obj_pending",
            grade=11,
            layer=2,
            category="kien_truc",
            anchor="P10-LOCAL-kien_truc-G11",
        )
        objects = {obj.object_id: obj}
        documented, needs_review = check_anchors(objects, anchor_registry)
        assert documented == 0
        assert needs_review == 1

    def test_documented_anchors_have_citations_and_are_few(self):
        registry = build_anchor_registry()
        counts = anchor_confidence_summary(registry)
        # Honesty budget: documented set stays minimal and citation-backed.
        assert counts["documented"] >= 1
        assert counts["documented"] < counts["needs_expert_review"]
        for anchor in registry.values():
            if anchor.confidence_status == "documented":
                citation = anchor.source_citation
                assert (
                    "32/2018" in citation
                    or "5512" in citation
                    or "backend/services" in citation
                ), anchor.anchor_code

    def test_anchor_without_citation_is_unconstructible(self):
        with pytest.raises(P10ContractError, match="source_citation"):
            CurriculumAnchor(
                anchor_code="NO-CITE",
                grade=10,
                competency_ref="x",
                source_citation="",
                confidence_status="documented",
            )


# ---------------------------------------------------------------------------
# Full-build guards on the real corpus
# ---------------------------------------------------------------------------
class TestFullBuildGuards:
    def test_proposed_builder_rejects_poisoned_cycle(self, corpus, anchor_registry):
        poisoned = list(corpus) + [
            make_object("obj_extra", grade=10, layer=1, category="dong_vat")
        ]
        edges = [
            PrerequisiteEdge("urn_cao_dinh_02", "obj_extra"),
            PrerequisiteEdge("obj_extra", "urn_cao_dinh_03"),
            PrerequisiteEdge("urn_cao_dinh_03", "urn_cao_dinh_02"),
        ]
        with pytest.raises(P10ContractError, match="violates invariants"):
            build_spiral_dag(poisoned, edges, anchor_registry)
