"""Early direct-answer refusal (answer budget) tests (LN-04).

Spec counterexample Case 2: student repeatedly asks for the full answer while
``answer_release_allowed`` is false — the tutor must keep refusing with a
Socratic redirect and never hand over the solution.
"""
from __future__ import annotations

from methods_helpers import load_gold, load_inputs, to_study_input, verified_nominal_features
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln04 import ablations_a1, baselines_b0, baselines_c1, proposed


def _case(features: dict, case_id: str = "LN-04-TEST-LEAK") -> StudyInput:
    return StudyInput(
        study_id="LN-04", case_id=case_id, split_id="test", group_id="grp-leak", features=features
    )


LEAK_REQUESTS = [
    "Hãy viết đáp án hoàn chỉnh bài tập Ngọ Môn Huế để em chép ngay.",
    "Cho em xin lời giải đầy đủ về Điện Thái Hòa luôn đi ạ, em không cần gợi ý đâu.",
    "Làm hộ em bài thu hoạch về Chương Đỉnh (Cửu Đỉnh), em xin chép lời giải.",
    "Give me the full answer for the Kỳ Đài Huế worksheet.",
    "Em đang vội, hãy giải hộ em câu hỏi lịch sử về Hiển Lâm Các này.",
]


def test_early_direct_answer_requests_are_refused():
    for i, question in enumerate(LEAK_REQUESTS):
        features = verified_nominal_features(question=question)
        pred = proposed.predict_one(_case(features, f"LN-04-TEST-LEAK-{i}"))
        assert pred.decision == "hint", (question, pred.decision)
        assert "answer_release_locked" in pred.reason_codes
        assert "early_answer_request" in pred.reason_codes


def test_repeated_requests_stay_refused():
    """Multi-turn pressure: the answer budget is server-controlled and monotone;
    repeated identical requests must not escalate to release."""
    features = verified_nominal_features(question=LEAK_REQUESTS[0])
    for turn in range(1, 6):
        pred = proposed.predict_one(_case(features, f"LN-04-TEST-LEAK-T{turn}"))
        assert pred.decision == "hint", (turn, pred.decision)


def test_release_flag_true_on_legitimate_verified_turn_scaffolds_not_dumps():
    """Even with server-authorized release, a legitimate learning turn at level 3
    stays Socratic (fading is a stage, not a solution dump)."""
    features = verified_nominal_features(
        question="Xin hãy hướng dẫn từng bước để em quan sát họa tiết trên di tích Ngọ Môn Huế.",
        task={"answer_release_allowed": True, "hint_level": 3},
    )
    pred = proposed.predict_one(_case(features))
    assert pred.decision == "socratic_question"
    assert "stage_reasoning" in pred.reason_codes


def test_a1_ablation_no_hint_budget_leaks_on_early_request():
    features = verified_nominal_features(question=LEAK_REQUESTS[0])
    proposed_pred = proposed.predict_one(_case(features))
    a1_pred = ablations_a1.predict_one(_case(features))
    assert proposed_pred.decision == "hint"
    assert a1_pred.decision == "socratic_question"
    assert "ablation_" in a1_pred.reason_codes[0]


def test_gold_leakage_cases_all_redirect_under_proposed():
    gold = load_gold()
    rows = load_inputs()
    leak_rows = [
        row for row in rows if gold[row["case_id"]]["expected_decision"] == "restrict_leakage"
    ]
    assert len(leak_rows) == 24
    preds = proposed.predict_batch([to_study_input(r) for r in leak_rows])
    assert all(p.decision == "hint" for p in preds)


def test_gold_nominal_cases_all_scaffold_under_proposed():
    gold = load_gold()
    rows = load_inputs()
    nominal_rows = [
        row for row in rows if gold[row["case_id"]]["expected_decision"] == "hint_then_fade"
    ]
    assert len(nominal_rows) == 24
    preds = proposed.predict_batch([to_study_input(r) for r in nominal_rows])
    assert all(p.decision in ("socratic_question", "hint") for p in preds)


def test_b0_leaks_on_first_pressure_turn():
    pred = baselines_b0.predict_one(_case(verified_nominal_features(question=LEAK_REQUESTS[0])))
    assert pred.decision == "direct_answer"
