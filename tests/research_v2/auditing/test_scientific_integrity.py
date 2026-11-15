"""Auditing tests: hash integrity, provenance, and no-oracle-leakage across holdouts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v2.contracts.canonical_hash import sha256_input
from research_v2.contracts.label_space import (
    ALLOWED_ORACLE_BASES,
    PROVENANCE_MARKER,
    SYNTHETIC_COHORT,
)

REPO = Path(__file__).resolve().parents[3]
HOLDOUT_DIR = REPO / "research" / "fixtures" / "holdout"
STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]


def _rows(study: str):
    path = HOLDOUT_DIR / f"{study}_holdout.jsonl"
    for line in path.open(encoding="utf-8"):
        if line.strip():
            yield json.loads(line)


def test_every_holdout_hash_matches_canonical_standard():
    bad = []
    total = 0
    for study in STUDY_IDS:
        for row in _rows(study):
            total += 1
            if row["input_hash"] != sha256_input(row["input"]):
                bad.append((study, row["case_id"]))
    assert total == 1200
    assert not bad, f"stale hashes: {bad[:10]}"


def test_holdout_cohorts_are_synthetic_labeled():
    for study in STUDY_IDS:
        for row in _rows(study):
            assert row["cohort"] == SYNTHETIC_COHORT, (study, row["case_id"])


def test_no_real_expert_claims_remain():
    for study in STUDY_IDS:
        for row in _rows(study):
            assert "external_expert_annotation" not in row
            basis = (row.get("oracle") or {}).get("basis")
            assert basis in ALLOWED_ORACLE_BASES, (study, row["case_id"], basis)
            assert row.get("annotation_provenance") == PROVENANCE_MARKER


def test_no_oracle_leakage_inside_input():
    for study in STUDY_IDS:
        for row in _rows(study):
            inp = row["input"]
            assert "oracle" not in inp, (study, row["case_id"])
            assert "expected_decision" not in inp, (study, row["case_id"])


def test_alternative_provider_counterexample_is_not_false_infeasible():
    """LN-06 P0 bug: A and B both provide T at 40 min, budget 50 -> feasible."""
    from research.heritage_trails.cognitive_route import HeritageStop, evaluate_route_intervention

    stops = [
        HeritageStop(id="a", cost=40, provides=("T",), requires=()),
        HeritageStop(id="b", cost=40, provides=("T",), requires=()),
    ]
    plan = evaluate_route_intervention(stops, ["a", "b"], ["T"], 50)
    assert plan.decision == "find_valid_route", plan.decision
    assert plan.route_cost == 40
    assert len(plan.stop_sequence) == 1


def test_ln04_b1_is_labeled_simulated_proxy():
    from research.baselines.strong_baselines import run_ln04_b1

    result = run_ln04_b1({"question": "Cho em đáp án bài này", "retrieval": {"source_ids": ["s1"], "source_status": "verified"}})
    assert result["baseline_type"] == "simulated_heuristic_llm_proxy"


# ---------------------------------------------------------------------------
# Evaluator boundary: oracle-free predictions + one-to-one coverage
# (research_v2/evaluation/metrics.py)
# ---------------------------------------------------------------------------

from research_v2.evaluation.metrics import (  # noqa: E402
    FORBIDDEN_GOLD_IN_PREDICTION,
    EvaluationError,
    compute_metrics,
)


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _clean_run(tmp_path: Path, *, n: int = 4) -> tuple[Path, Path]:
    golds = [{"case_id": f"c{i}", "expected_decision": "accept" if i % 2 else "reject"} for i in range(n)]
    preds = [
        {"case_id": f"c{i}", "decision": golds[i]["expected_decision"]}
        for i in range(n)
    ]
    gold_path = _write_jsonl(tmp_path / "gold.jsonl", golds)
    pred_path = _write_jsonl(tmp_path / "preds.jsonl", preds)
    return pred_path, gold_path


def test_forbidden_set_covers_expanded_gold_keys():
    expanded = {
        "gold", "label", "labels", "cohort", "expected_outcome",
        "expected_conclusion", "oracle_basis", "annotation_provenance",
        "synthetic_annotation_template", "external_expert_annotation",
        "correct", "is_correct",
    }
    assert expanded <= FORBIDDEN_GOLD_IN_PREDICTION


def test_prediction_with_top_level_gold_key_is_rejected(tmp_path):
    pred_path, gold_path = _clean_run(tmp_path)
    _write_jsonl(pred_path, [{"case_id": "c0", "decision": "accept", "gold": "accept"}])
    with pytest.raises(EvaluationError, match="gold material"):
        compute_metrics(pred_path, gold_path)


@pytest.mark.parametrize(
    "key",
    [
        "oracle",
        "expected_decision",
        "expected_category",
        "fault_id",
        "gold_label",
        "gold",
        "label",
        "labels",
        "cohort",
        "expected_outcome",
        "expected_conclusion",
        "oracle_basis",
        "annotation_provenance",
        "synthetic_annotation_template",
        "external_expert_annotation",
        "correct",
        "is_correct",
    ],
)
def test_prediction_with_each_forbidden_top_level_key_is_rejected(tmp_path, key):
    pred_path, gold_path = _clean_run(tmp_path)
    _write_jsonl(pred_path, [{"case_id": "c0", "decision": "accept", key: "x"}])
    with pytest.raises(EvaluationError, match="gold material"):
        compute_metrics(pred_path, gold_path)


def test_prediction_with_nested_meta_oracle_is_rejected(tmp_path):
    """Gold smuggled inside a nested dict is still gold material."""
    pred_path, gold_path = _clean_run(tmp_path)
    _write_jsonl(
        pred_path,
        [{"case_id": "c0", "decision": "accept", "meta": {"oracle": {"expected_decision": "accept"}}}],
    )
    with pytest.raises(EvaluationError, match="gold material"):
        compute_metrics(pred_path, gold_path)


def test_prediction_with_nested_gold_in_list_is_rejected(tmp_path):
    pred_path, gold_path = _clean_run(tmp_path)
    _write_jsonl(
        pred_path,
        [{"case_id": "c0", "decision": "accept", "traces": [{"is_correct": True}]}],
    )
    with pytest.raises(EvaluationError, match="gold material"):
        compute_metrics(pred_path, gold_path)


def test_extra_prediction_not_in_gold_is_rejected(tmp_path):
    pred_path, gold_path = _clean_run(tmp_path, n=3)
    preds = [{"case_id": f"c{i}", "decision": "accept"} for i in range(3)]
    preds.append({"case_id": "c_extra", "decision": "reject"})
    _write_jsonl(pred_path, preds)
    with pytest.raises(EvaluationError, match="extra predictions"):
        compute_metrics(pred_path, gold_path)


def test_duplicate_case_id_in_predictions_is_rejected(tmp_path):
    pred_path, gold_path = _clean_run(tmp_path)
    _write_jsonl(
        pred_path,
        [
            {"case_id": "c0", "decision": "accept"},
            {"case_id": "c0", "decision": "reject"},
        ],
    )
    with pytest.raises(EvaluationError, match="duplicate case_id in predictions"):
        compute_metrics(pred_path, gold_path)


def test_duplicate_case_id_in_gold_is_rejected(tmp_path):
    pred_path, gold_path = _clean_run(tmp_path)
    _write_jsonl(
        gold_path,
        [
            {"case_id": "c0", "expected_decision": "accept"},
            {"case_id": "c0", "expected_decision": "reject"},
        ],
    )
    with pytest.raises(EvaluationError, match="duplicate case_id in gold"):
        compute_metrics(pred_path, gold_path)


def test_valid_clean_run_returns_metrics_with_intervals(tmp_path):
    pred_path, gold_path = _clean_run(tmp_path, n=4)
    result = compute_metrics(pred_path, gold_path)
    assert result["n_total"] == 4
    assert result["n_correct"] == 4
    assert result["accuracy"] == 1.0
    assert "accuracy_wilson_ci_95" in result and result["accuracy_wilson_ci_95"] is not None
    assert "accuracy_clopper_pearson_ci_95" in result
    assert result["accuracy_clopper_pearson_ci_95"] is not None
    for bound in result["accuracy_clopper_pearson_ci_95"]:
        assert 0.0 <= bound <= 1.0
    assert result["error_rate_wilson_ci_95"] is not None
    assert result["error_rate_clopper_pearson_ci_95"] is not None


def test_missing_prediction_still_rejected(tmp_path):
    """Regression guard: the original one-sided coverage check is preserved."""
    pred_path, gold_path = _clean_run(tmp_path, n=3)
    _write_jsonl(pred_path, [{"case_id": f"c{i}", "decision": "accept"} for i in range(2)])
    with pytest.raises(EvaluationError, match="missing predictions"):
        compute_metrics(pred_path, gold_path)
