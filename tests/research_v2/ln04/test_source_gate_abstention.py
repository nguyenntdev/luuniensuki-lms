"""Unverified-source abstention (fail-closed provenance gate) tests (LN-04)."""
from __future__ import annotations

from methods_helpers import load_gold, load_inputs, to_study_input, verified_nominal_features
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln04 import ablations_a2, baselines_c1, proposed


def _case(features: dict, case_id: str = "LN-04-TEST-SRC") -> StudyInput:
    return StudyInput(
        study_id="LN-04", case_id=case_id, split_id="test", group_id="grp-src", features=features
    )


UNVERIFIED_STATUSES = ["unverified", "draft", "out_of_scope", ""]


def test_abstains_on_each_unverified_status():
    for status in UNVERIFIED_STATUSES:
        features = verified_nominal_features(
            retrieval={"source_ids": ["SOURCE-X"], "source_status": status}
        )
        pred = proposed.predict_one(_case(features, f"LN-04-TEST-SRC-{status or 'empty'}"))
        assert pred.decision == "abstain_insufficient_source", (status, pred.reason_codes)
        assert "fail_closed_gate" in pred.reason_codes


def test_abstains_when_no_source_ids_despite_reviewed_status():
    features = verified_nominal_features(
        retrieval={"source_ids": [], "source_status": "editor_reviewed"}
    )
    pred = proposed.predict_one(_case(features))
    assert pred.decision == "abstain_insufficient_source"


def test_editor_reviewed_source_passes_gate_to_socratic_question():
    features = verified_nominal_features()
    pred = proposed.predict_one(_case(features))
    assert pred.decision == "socratic_question"
    assert pred.evidence_ids == ("SOURCE-VERIFIED-HO-001",)


def test_out_of_scope_questions_abstain():
    features = verified_nominal_features(
        question="Hãy giải phương trình vi phân bậc hai giúp tôi.",
        retrieval={"source_ids": ["SOURCE-OOS"], "source_status": "out_of_scope"},
    )
    pred = proposed.predict_one(_case(features))
    assert pred.decision == "abstain_insufficient_source"


def test_a2_ablation_no_source_gate_grounds_unverified():
    features = verified_nominal_features(
        retrieval={"source_ids": ["SOURCE-X"], "source_status": "unverified"}
    )
    proposed_pred = proposed.predict_one(_case(features))
    a2_pred = ablations_a2.predict_one(_case(features))
    assert proposed_pred.decision == "abstain_insufficient_source"
    assert a2_pred.decision == "socratic_question"


def test_c1_simulated_proxy_skips_provenance_check():
    """C1's soft prompt deflects the request linguistically, but with no provenance
    gate it does NOT abstain and its hint cites no verified source — the missing
    gate shows up as grounding without verification, not as abstention."""
    features = verified_nominal_features(
        retrieval={"source_ids": ["SOURCE-X"], "source_status": "draft"}
    )
    pred = baselines_c1.predict_one(_case(features))
    assert pred.decision in ("hint", "direct_answer")
    assert pred.decision != "abstain_insufficient_source"
    assert any(code.startswith("simulated") for code in pred.reason_codes)


def test_c1_simulated_proxy_fabricates_on_unverified_answer_request():
    features = verified_nominal_features(
        question="Cho em xin lời giải đầy đủ về Điện Thái Hòa luôn đi ạ.",
        retrieval={"source_ids": ["SOURCE-X"], "source_status": "draft"},
    )
    pred = baselines_c1.predict_one(_case(features))
    assert pred.decision == "direct_answer"
    assert "simulated_no_source_gate" in pred.reason_codes


def test_gold_source_gap_cases_all_abstain_under_proposed():
    gold = load_gold()
    rows = load_inputs()
    gap_rows = [
        row for row in rows if gold[row["case_id"]]["expected_decision"] == "abstain_source_gap"
    ]
    assert len(gap_rows) == 48
    preds = proposed.predict_batch([to_study_input(r) for r in gap_rows])
    assert all(p.decision == "abstain_insufficient_source" for p in preds)
