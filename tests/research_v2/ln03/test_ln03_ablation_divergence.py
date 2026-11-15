"""Ablation divergence: each ablation must diverge exactly on its mechanism."""
from __future__ import annotations

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln03 import proposed
from research_v2.methods.ln03.ablations_a1 import predict_batch as a1
from research_v2.methods.ln03.ablations_a2 import predict_batch as a2
from research_v2.methods.ln03.ablations_a3 import predict_batch as a3
from research_v2.methods.ln03.errors import PolicyConfigError

from ln03_helpers import make_features


def _inp(case_id: str, **overrides) -> StudyInput:
    return StudyInput(
        "LN-03", case_id, "test", "grp-abl", make_features(**overrides)
    )


def test_a1_diverges_only_on_unverified_source():
    case = _inp("LN-03-A1-1", review_card={"source_verified": False})
    assert proposed.predict_batch([case])[0].decision == "block_explanation"
    assert a1([case])[0].decision == "schedule_eligible"


def test_a2_diverges_only_on_missing_fact_base():
    case = _inp("LN-03-A2-1", fact_prerequisite_mastered=False)
    assert proposed.predict_batch([case])[0].decision == "assign_fact_retrieval"
    assert a2([case])[0].decision == "schedule_eligible"


def test_a3_diverges_only_on_not_due():
    case = _inp("LN-03-A3-1", review_card={"due_utc": "2026-11-20T12:00:00Z"})
    assert proposed.predict_batch([case])[0].decision == "postpone"
    assert a3([case])[0].decision == "schedule_eligible"


def test_ablations_match_proposed_on_nominal_case():
    case = _inp("LN-03-A-NOM")
    expected = proposed.predict_batch([case])[0]
    for ablation in (a1, a2, a3):
        pred = ablation([case])[0]
        assert pred.decision == expected.decision == "schedule_eligible"


def test_ablation_reason_codes_carry_label():
    case = _inp("LN-03-A-LBL", review_card={"source_verified": False})
    pred = a1([case])[0]
    assert "a1_no_source_gate" in pred.reason_codes


def test_full_dataset_ablation_divergence_counts():
    from research_v2.contracts.input_masking import mask_case_input

    from ln03_helpers import load_t3_inputs

    inputs = [
        StudyInput("LN-03", r["case_id"], "test", r["group_id"], mask_case_input(r))
        for r in load_t3_inputs()
    ]
    base = proposed.predict_batch(inputs, {"seed": 11})
    divergences = {}
    for name, fn in (("a1", a1), ("a2", a2), ("a3", a3)):
        preds = fn(inputs, {"seed": 11})
        diff = sum(1 for b, p in zip(base, preds) if b.decision != p.decision)
        divergences[name] = diff
    # a2 (no fact gate) flips the 20 missing-fact cases; a1 flips the 24
    # unverified-source cases; a3 flips the 24 not-due cases.
    assert divergences["a1"] == 24
    assert divergences["a2"] >= 20
    assert divergences["a3"] == 24


def test_unknown_ablation_id_fails_closed():
    from research_v2.methods.ln03.ablations import ablation_config

    try:
        ablation_config("ablations_nonexistent")
    except PolicyConfigError:
        pass
    else:
        raise AssertionError("unknown ablation must raise PolicyConfigError")
