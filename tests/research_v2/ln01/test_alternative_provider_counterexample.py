"""Mandatory counterexample: two alternative providers of the same outcome.

Two nodes carry the SAME learning outcome (same content_id + objective) and the
graph links them with cross edges (0->1, 1->0 plus entry/exit edges). The pair
is redundant, not infeasible: a route exists by selecting one provider. The
legacy engine's per-edge strict Bloom-increase rule plus its cycle extraction
falsely rejects this family (reject_no_progression / reject_cycle). The V2
proposed method must NOT false-reject (no false infeasibility).
"""
from __future__ import annotations

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln01.proposed import predict_batch as proposed_batch
from research_v2.methods.ln01.baselines import predict_batch_b0, predict_batch_c1
from research_v2.methods.ln01 import ablations


def _alternative_provider_input(case_id: str = "case-alt-providers") -> StudyInput:
    """Nodes 0 and 1 are alternative providers of the same outcome; nodes 2 and 3
    are genuine progression steps reached after either provider.

    Edges: 0<->1 (provider cross-links), 1->2 (progression), 2->3 (progression).
    A feasible route is e.g. 0 -> 2 -> 3 (skipping the redundant 1).
    """
    features = {
        "nodes": [
            {"content_id": "tuyen-dinh", "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
            {"content_id": "tuyen-dinh", "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
            {"content_id": "tuyen-dinh", "grade": 11, "cognitive_level": 3, "objective": "source_corroboration"},
            {"content_id": "tuyen-dinh", "grade": 12, "cognitive_level": 4, "objective": "heritage_evaluation"},
        ],
        "prerequisites": [[0, 1], [1, 0], [1, 2], [2, 3]],
        "curriculum_anchor": {
            "grade10": "GDĐP-HUE-10-ART",
            "grade11": "GDĐP-HUE-11-HISTORY",
            "grade12": "GDĐP-HUE-12-HERITAGE",
        },
    }
    return StudyInput("LN-01", case_id, "test", "grp-alt", features)


def test_alternative_providers_must_not_be_false_infeasible():
    pred = proposed_batch([_alternative_provider_input()], {})[0]
    assert pred.decision == "accept", (
        f"false infeasibility: {pred.decision} with reasons {pred.reason_codes}"
    )


def test_self_loop_between_duplicate_providers_is_also_benign():
    features = dict(_alternative_provider_input().features)
    features["prerequisites"] = [[0, 0], [1, 0], [0, 2], [2, 3]]
    pred = proposed_batch([StudyInput("LN-01", "alt-self", "test", "grp-alt", features)], {})[0]
    assert pred.decision == "accept"


def test_progression_cycle_still_rejected_even_with_duplicate_providers():
    """A cycle through a real progression edge is a true contradiction."""
    features = dict(_alternative_provider_input().features)
    features["prerequisites"] = [[0, 1], [1, 0], [1, 2], [2, 3], [3, 2]]
    pred = proposed_batch([StudyInput("LN-01", "alt-true-cycle", "test", "grp-alt", features)], {})[0]
    assert pred.decision == "reject_cycle"


def test_c1_topological_baseline_falsely_rejects_benign_provider_cycle():
    """Documented legacy-bug reproduction: C1 is a faithful Kahn topological
    baseline. The provider cross-cycle makes Kahn's sort infeasible even though
    a feasible route exists by selecting one provider, so C1 false-rejects.
    This is exactly the false-infeasibility gap the proposed method closes —
    the comparative divergence is the scientifically expected result."""
    pred = predict_batch_c1([_alternative_provider_input()], {})[0]
    assert pred.decision == "reject_cycle"


def test_ablation_without_depth_gate_also_accepts_but_proposed_differs_on_flat_cases():
    """The ablation-a3 (no depth gate) differs from proposed only on flat-progression
    cases; on THIS case both accept, and b0 accepts everything. The difference is
    covered by test_ablations_differ.py."""
    pred = ablations.predict_batch([_alternative_provider_input()], {})[0]
    flat = proposed_batch([_alternative_provider_input()], {})[0]
    assert pred.decision == "accept"
    assert flat.decision == "accept"


def test_b0_sanity_accepts_everything_including_true_cycle():
    features = dict(_alternative_provider_input().features)
    features["prerequisites"] = [[0, 1], [1, 2], [2, 0]]
    pred = predict_batch_b0([StudyInput("LN-01", "alt-cyc", "test", "grp-alt", features)], {})[0]
    assert pred.decision == "accept"
