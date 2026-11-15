"""Every ablation must genuinely change the decision path versus the proposed
method on a case that exercises exactly the removed mechanism."""
from __future__ import annotations

from research_v2.methods.ln01.proposed import predict_batch as proposed_batch
from research_v2.methods.ln01 import ablations, ablations_a2, ablations_a3

from ln01_helpers import make_features, make_input

CYCLE_FEATS = make_features(prerequisites=[[0, 1], [1, 2], [2, 0]])
ANCHOR_FEATS = make_features(curriculum_anchor={"grade10": "GDĐP-HUE-10-ART", "grade11": "", "grade12": "GDĐP-HUE-12-HERITAGE"})
FLAT_FEATS = make_features(
    nodes=[
        {"content_id": "cao-dinh", "grade": 10, "cognitive_level": 1, "objective": "motif_observation"},
        {"content_id": "cao-dinh", "grade": 10, "cognitive_level": 1, "objective": "motif_observation_repeated"},
        {"content_id": "cao-dinh", "grade": 11, "cognitive_level": 3, "objective": "source_corroboration"},
    ],
    prerequisites=[[0, 1], [1, 2]],
)


def test_a1_no_cycle_check_loses_the_precise_cycle_certificate():
    """With the cycle check removed, a1 can no longer emit ``reject_cycle``.

    A true cycle necessarily contains at least one non-increasing Bloom edge
    (a closed loop cannot strictly ascend), so the downstream depth gate fires
    and a1 degrades to a coarser certificate (``reject_no_progression`` or
    ``reject_grade_order``). The certificate itself is the ablation difference:
    proposed gives the exact root cause, a1 misattributes it.
    """
    proposed = proposed_batch([make_input("a1p", CYCLE_FEATS)], {})[0]
    ablated = ablations.predict_batch([make_input("a1a", CYCLE_FEATS)], {})[0]
    assert proposed.decision == "reject_cycle"
    assert ablated.decision in {"reject_no_progression", "reject_grade_order", "accept"}
    assert ablated.decision != proposed.decision


def test_a2_no_crosswalk_accepts_missing_anchor():
    proposed = proposed_batch([make_input("a2p", ANCHOR_FEATS)], {})[0]
    ablated = ablations_a2.predict_batch([make_input("a2a", ANCHOR_FEATS)], {})[0]
    assert proposed.decision == "reject_missing_anchor"
    assert ablated.decision == "accept"


def test_a3_no_depth_gate_accepts_flat_progression():
    proposed = proposed_batch([make_input("a3p", FLAT_FEATS)], {})[0]
    ablated = ablations_a3.predict_batch([make_input("a3a", FLAT_FEATS)], {})[0]
    assert proposed.decision == "reject_no_progression"
    assert ablated.decision == "accept"


def test_ablations_never_differ_on_nominal_case():
    """Ablations must not manufacture differences on nominal inputs."""
    nominal = make_input("nom", make_features())
    for fn in (ablations.predict_batch, ablations_a2.predict_batch, ablations_a3.predict_batch):
        assert fn([nominal], {})[0].decision == "accept"
