"""P10 ablation mechanism-sensitivity tests (packet §5: A1-A4)."""
from __future__ import annotations

from research_v3.methods.p10.ablations import (
    run_a1_no_layer_bridge,
    run_a2_no_bloom_ascent,
    run_a3_no_provenance_gate,
    run_a4_random_order,
)
from research_v3.methods.p10.corpus import build_prerequisite_edges
from research_v3.methods.p10.spiral_builder import build_spiral_dag


class TestA1NoLayerBridge:
    def test_removing_bridges_disconnects_urns(self, corpus, anchor_registry):
        """Sensitivity: with bridges the edge-referenceable object graph forms
        one connected component; without them it shatters (>= 9 components)."""
        full_edges = build_prerequisite_edges(corpus)
        proposed = build_spiral_dag(corpus, full_edges, anchor_registry)
        assert proposed.certificate.valid
        a1, notes = run_a1_no_layer_bridge(corpus, anchor_registry)
        full_census = _components_with_bridges(corpus)
        no_bridge_census = notes["component_census"]
        assert no_bridge_census["edge_connected_components"] >= 9
        assert full_census["edge_connected_components"] < no_bridge_census["edge_connected_components"]

    def test_a1_order_differs_from_proposed(self, corpus, anchor_registry):
        full_edges = build_prerequisite_edges(corpus)
        proposed = build_spiral_dag(corpus, full_edges, anchor_registry)
        a1, _ = run_a1_no_layer_bridge(corpus, anchor_registry)
        assert a1.ordered_object_ids != proposed.ordered_object_ids


class TestA2NoBloomAscent:
    def test_certificate_stops_asserting_depth(self, corpus, anchor_registry):
        proposed = build_spiral_dag(
            corpus, build_prerequisite_edges(corpus), anchor_registry
        )
        assert proposed.certificate.bloom_ascent_ok
        a2, notes = run_a2_no_bloom_ascent(corpus, anchor_registry)
        # The gate is REMOVED, so the certificate field flips to False by design
        # (the design no longer makes a depth claim), while the measured edge
        # ascent rate is recorded for comparison.
        assert not a2.certificate.bloom_ascent_ok
        assert 0.0 <= notes["progression_strict_ascent_rate"] <= 1.0


class TestA3NoProvenanceGate:
    def test_gate_off_lets_fabricated_anchor_through(self, corpus, anchor_registry):
        """The negative demonstration: without the anchor gate, an invented
        competency code silently enters the sequence — the exact failure the
        proposed design closes."""
        a3, notes = run_a3_no_provenance_gate(corpus, anchor_registry)
        assert notes["invented_anchor_accepted"] is True
        assert "urn_poisoned_fabricated_anchor_01" in a3.ordered_object_ids

    def test_gate_on_rejects_the_same_object(self, corpus, anchor_registry):
        """Symmetry check: the proposed (gate-on) builder raises on the same
        poisoned object instead of accepting it."""
        import pytest

        from research_v3.methods.p10.anchors import LearningObject, P10ContractError

        poison = LearningObject(
            object_id="urn_poisoned_fabricated_anchor_01",
            urn_slug="cao-dinh",
            motif_name_vi="Họa tiết bị gắn mã năng lực bịa",
            category="linh_thu",
            grade=10,
            layer=1,
            bloom_level=2,
            anchor_code="NH10-FABRICATED-COMPETENCY",
        )
        with pytest.raises(P10ContractError, match="UnknownAnchorError|not in the frozen"):
            build_spiral_dag(list(corpus) + [poison], build_prerequisite_edges(list(corpus) + [poison]), anchor_registry)


class TestA4RandomOrder:
    def test_random_playlist_fails_grade_monotonicity(self, corpus, anchor_registry):
        a4, notes = run_a4_random_order(corpus, anchor_registry, seed=42)
        assert not a4.certificate.valid
        assert notes["playlist_grade_inversions"] > 0

    def test_seeded_reproducible(self, corpus, anchor_registry):
        a1, n1 = run_a4_random_order(corpus, anchor_registry, seed=123)
        a2, n2 = run_a4_random_order(corpus, anchor_registry, seed=123)
        assert a1.ordered_object_ids == a2.ordered_object_ids
        assert n1 == n2


# ---------------------------------------------------------------------------
def _components_with_bridges(corpus) -> dict:
    from research_v3.methods.p10.ablations import _weakly_connected_components
    from research_v3.methods.p10.corpus import build_prerequisite_edges

    idx = {o.object_id: o for o in corpus}
    return _weakly_connected_components(idx, build_prerequisite_edges(corpus))
