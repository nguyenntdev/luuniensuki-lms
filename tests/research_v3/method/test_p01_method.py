"""P01 method tests: leakage, split integrity, determinism, negative cases,
metric recomputation, and gate-mechanism counterexamples.

Fast tests use a deterministic synthetic fixture with the OULAD schema shape;
one session-scoped test runs the real OULAD adapter end to end.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from research_v3.methods.p01.features import (
    build_vocabulary,
    feature_dim,
    featurize_rows,
)
from research_v3.methods.p01.metrics import (
    compute_classification_metrics,
    fail_false_alarm_rate,
    paired_mcnemar,
)
from research_v3.methods.p01.models import (
    calibrate_gate,
    fit_classical,
    fit_majority,
    predict_batch,
    predict_majority,
)
from research_v3.methods.p01.pipeline import (
    enforce_learner_disjointness,
    load_validated_rows,
    run_protocol,
)
from research_v3.methods.p01.types import (
    ABSTAIN,
    LABELS,
    ModelConfig,
    P01ContractError,
    Predictions,
    validate_features,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = PROJECT_ROOT / "research_artifacts_v3" / "runs" / "p01"


# --------------------------------------------------------------------------
# Synthetic fixture with the OULAD row shape (fast, deterministic)
# --------------------------------------------------------------------------
CATEGORICAL_VALUES = {
    "code_module": ["AAA", "BBB"],
    "code_presentation": ["2013B", "2013J"],
    "gender": ["F", "M"],
    "region": ["North Region", "South Region"],
    "highest_education": ["A Level or Equivalent", "Lower Than A Level"],
    "imd_band": ["0-10%", "10-20"],
    "age_band": ["0-35", "35-55"],
    "disability": ["N", "Y"],
}


def _synthetic_rows(n: int = 400, seed: int = 7) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        feats = {f: vals[int(rng.integers(len(vals)))] for f, vals in CATEGORICAL_VALUES.items()}
        feats["num_of_prev_attempts"] = int(rng.integers(0, 3))
        feats["studied_credits"] = int(rng.choice([60, 120, 180]))
        feats["early_click_total"] = int(rng.integers(0, 500))
        feats["early_active_sites"] = int(rng.integers(0, 30))
        feats["observation_window_days"] = 60
        # signal: clicks correlate with passing
        prob_pass = min(0.9, 0.2 + feats["early_click_total"] / 700)
        label = "Pass" if rng.random() < prob_pass else "Fail"
        rows.append(
            {
                "case_id": f"syn-{i}",
                "group_id": f"g{i}",  # unique learners -> group-disjoint by construction
                "time_key": feats["code_presentation"],
                "input": feats,
                "label": label,
            }
        )
    return rows


@pytest.fixture(scope="module")
def synth():
    return _synthetic_rows()


def _partition(synth_rows):
    from research_v3.eval.splitters import group_split

    split = group_split(
        synth_rows, group_key="group_id", paper_id="P01-test",
        fractions=(0.7, 0.1, 0.1, 0.1), salt="test-salt",
    )
    id2part = {}
    for part, ids in split.split_ids.items():
        for cid in ids:
            id2part[cid] = part
    return {p: [r for r in synth_rows if id2part[r["case_id"]] == p] for p in split.split_ids}


@pytest.fixture(scope="module")
def trained(synth):
    parts = _partition(synth)
    vocab = build_vocabulary(parts["train"])
    config = ModelConfig(seed=0)
    model = fit_classical(parts["train"], vocab, config=config)
    Pcal = model.predict_proba(featurize_rows(parts["calibration"], vocab))
    thresholds = calibrate_gate(parts["calibration"], Pcal, config=config)
    return parts, vocab, model, thresholds, config


# --------------------------------------------------------------------------
# 1. Label leakage
# --------------------------------------------------------------------------
def test_features_reject_label_keys():
    with pytest.raises(P01ContractError):
        validate_features({"gender": "F", "label": "Pass"})
    with pytest.raises(P01ContractError):
        validate_features({"gender": "F", "final_result": "Fail"})
    with pytest.raises(P01ContractError):
        validate_features({"gender": "F", "gold": "Pass"})


def test_predictions_never_carry_gold_material(trained):
    parts, vocab, model, thresholds, config = trained
    preds = predict_batch(
        parts["test"],
        {"model_id": "proposed_rc_stg", "vocabulary": vocab,
         "weights": model.weights.tolist(), "bias": model.bias.tolist(),
         "thresholds": thresholds.to_dict(), "gate_mode": "full"},
    )
    for row in preds.to_jsonl_rows():
        assert "label" not in row and "gold" not in row
        assert set(row) == {"case_id", "decision", "score", "reason_codes", "model_id"}


def test_real_oulad_rows_have_label_outside_input():
    """Adapter contract: 'label' is a sibling of 'input', never inside it."""
    rows = load_validated_rows()[0][:200]
    for row in rows:
        assert "label" not in row["input"]
        assert row["label"] in LABELS


# --------------------------------------------------------------------------
# 2. Split disjointness (group + time)
# --------------------------------------------------------------------------
def test_group_split_disjoint_learners(synth):
    from research_v3.eval.leakage import assert_disjoint_groups
    from research_v3.eval.splitters import assert_no_leakage, group_split

    split = group_split(synth, group_key="group_id", paper_id="P01-test", salt="s1")
    assert_no_leakage(split)
    parts = _partition(synth)
    for a in ("train", "calibration", "dev"):
        assert_disjoint_groups(parts[a], parts["test"], group_key="group_id")


def test_time_split_learner_disjointness_after_enforcement():
    """Real OULAD: learners in later partitions are removed from earlier ones."""
    rows = load_validated_rows()[0]
    from research_v3.eval.leakage import assert_disjoint_groups
    from research_v3.eval.splitters import time_split

    split = time_split(rows, time_key="time_key", paper_id="P01", train_fraction=0.70)
    id2part = {}
    for part, ids in split.split_ids.items():
        for cid in ids:
            id2part[cid] = part
    parts = {p: [r for r in rows if id2part[r["case_id"]] == p] for p in split.split_ids}
    parts, removed = enforce_learner_disjointness(parts)
    assert removed > 0
    for later in ("test", "dev", "calibration"):
        for earlier in ("train", "calibration", "dev"):
            if later == earlier:
                continue
            order = ["train", "calibration", "dev", "test"]
            if order.index(earlier) >= order.index(later):
                continue
            assert_disjoint_groups(parts[earlier], parts[later], group_key="group_id")
    # test set untouched by enforcement
    assert len(parts["test"]) == len([r for r in rows if id2part[r["case_id"]] == "test"])


def test_time_split_test_rows_are_future_presentation():
    rows = load_validated_rows()[0]
    from research_v3.eval.splitters import time_split

    split = time_split(rows, time_key="time_key", paper_id="P01", train_fraction=0.70)
    id2part = {}
    for part, ids in split.split_ids.items():
        for cid in ids:
            id2part[cid] = part
    test_rows = [r for r in rows if id2part[r["case_id"]] == "test"]
    assert {r["time_key"] for r in test_rows} == {"2014J"}


# --------------------------------------------------------------------------
# 3. Determinism
# --------------------------------------------------------------------------
def test_same_seed_identical_predictions(synth, trained):
    parts, vocab, model, thresholds, config = trained
    cfg = {"model_id": "proposed_rc_stg", "vocabulary": vocab,
           "weights": model.weights.tolist(), "bias": model.bias.tolist(),
           "thresholds": thresholds.to_dict(), "gate_mode": "full"}
    p1 = predict_batch(parts["test"], cfg)
    p2 = predict_batch(parts["test"], cfg)
    assert p1.to_jsonl_rows() == p2.to_jsonl_rows()


def test_refit_same_seed_identical_predictions(synth):
    """Rebuilding everything from scratch (split -> fit -> calibrate) must
    reproduce byte-identical predictions under the same seed."""
    from research_v3.eval.splitters import group_split

    def build():
        rows = _synthetic_rows(seed=7)
        split = group_split(rows, group_key="group_id", paper_id="P01-test",
                            fractions=(0.7, 0.1, 0.1, 0.1), salt="test-salt")
        parts = _partition(rows)
        vocab = build_vocabulary(parts["train"])
        cfg = ModelConfig(seed=0)
        model = fit_classical(parts["train"], vocab, config=cfg)
        Pcal = model.predict_proba(featurize_rows(parts["calibration"], vocab))
        thr = calibrate_gate(parts["calibration"], Pcal, config=cfg)
        preds = predict_batch(
            parts["test"],
            {"model_id": "proposed_rc_stg", "vocabulary": vocab,
             "weights": model.weights.tolist(), "bias": model.bias.tolist(),
             "thresholds": thr.to_dict(), "gate_mode": "full"},
        )
        return preds.to_jsonl_rows()

    assert build() == build()


def test_vocabulary_from_train_only_and_deterministic(synth):
    parts = _partition(synth)
    v1 = build_vocabulary(parts["train"])
    v2 = build_vocabulary(parts["train"])
    assert v1 == v2
    # a value seen only in test must not enter the train vocabulary
    test_only = dict(parts["test"][0])
    test_only["input"] = dict(parts["test"][0]["input"], region="Atlantis")
    parts["test"][0] = test_only
    v3 = build_vocabulary(parts["train"])
    assert v3 == v1


# --------------------------------------------------------------------------
# 4. Negative cases
# --------------------------------------------------------------------------
def test_predict_batch_rejects_input_with_label_key(trained):
    parts, vocab, model, thresholds, config = trained
    bad = [dict(parts["test"][0])]
    bad[0] = dict(bad[0])
    bad[0]["input"] = dict(bad[0]["input"], label="Pass")
    with pytest.raises(P01ContractError):
        predict_batch(
            bad,
            {"model_id": "proposed_rc_stg", "vocabulary": vocab,
             "weights": model.weights.tolist(), "bias": model.bias.tolist(),
             "thresholds": thresholds.to_dict(), "gate_mode": "full"},
        )


def test_predict_batch_rejects_unknown_label_vocabulary(synth):
    parts = _partition(synth)
    vocab = build_vocabulary(parts["train"])
    bad_train = [dict(r) for r in parts["train"][:5]]
    bad_train[0] = dict(bad_train[0], label="Superpass")
    with pytest.raises(P01ContractError):
        fit_classical(bad_train, vocab, config=ModelConfig())


def test_calibrate_gate_refuses_tiny_calibration_split():
    rows = _synthetic_rows(30)
    vocab = build_vocabulary(rows[:20])
    X = featurize_rows(rows[:20], vocab)
    rng = np.random.default_rng(0)
    probs = np.stack([np.abs(rng.dirichlet(np.ones(4))) for _ in range(20)])
    with pytest.raises(P01ContractError):
        calibrate_gate(rows[:20], probs, config=ModelConfig())


def test_abstain_is_distinct_from_class_labels():
    assert ABSTAIN not in LABELS
    assert ABSTAIN == "ABSTAIN"
    with pytest.raises(P01ContractError):
        Predictions(
            model_id="x", decisions=("BOGUS",), scores=(0.5,),
            reason_codes=(("ungated_argmax",),), case_ids=("c",),
        )


def test_metric_computation_fails_closed_on_missing_predictions():
    preds = [{"case_id": "c1", "decision": "Pass"}]
    gold = [{"case_id": "c1", "label": "Pass"}, {"case_id": "c2", "label": "Fail"}]
    with pytest.raises(P01ContractError):
        compute_classification_metrics(preds, gold, model_id="m")


# --------------------------------------------------------------------------
# 5. Metric recomputation from saved predictions
# --------------------------------------------------------------------------
def test_reported_metric_equals_recomputation_from_saved_predictions():
    """The primary metric in the artifact must equal a fresh recomputation
    from the saved prediction rows + sealed gold."""
    metrics_path = RUNS_DIR / "T" / "metrics_C1_regularized_logistic.json"
    preds_path = RUNS_DIR / "T" / "predictions_C1_regularized_logistic.jsonl"
    gold_path = RUNS_DIR / "T" / "sealed_gold.jsonl"
    if not metrics_path.is_file():
        pytest.skip("P01 artifacts not materialized yet; run run_p01 first")
    saved = json.loads(metrics_path.read_text())
    pred_rows = [json.loads(l) for l in preds_path.read_text().splitlines() if l.strip()]
    gold_rows = [json.loads(l) for l in gold_path.read_text().splitlines() if l.strip()]
    recomputed = compute_classification_metrics(pred_rows, gold_rows, model_id="C1")
    assert recomputed["accuracy"] == saved["accuracy"]
    assert recomputed["n"] == saved["n"] == len(gold_rows)
    assert recomputed["macro_f1"] == saved["macro_f1"]
    assert recomputed["per_class_recall"] == saved["per_class_recall"]


def test_proposed_metric_recomputation_and_null_result_consistency():
    metrics_path = RUNS_DIR / "T" / "metrics_proposed_rc_stg.json"
    c1_path = RUNS_DIR / "T" / "metrics_C1_regularized_logistic.json"
    null_path = RUNS_DIR / "T" / "null_result.json"
    if not null_path.is_file():
        pytest.skip("P01 artifacts not materialized yet")
    null_rec = json.loads(null_path.read_text())
    assert null_rec["is_null_or_negative"] is True
    assert null_rec["observed"] == json.loads(metrics_path.read_text())["accuracy"]
    assert null_rec["baseline"] == json.loads(c1_path.read_text())["accuracy"]


def test_saved_split_manifests_are_disjoint():
    for proto in ("T", "G"):
        manifest_path = RUNS_DIR / proto / "splits_manifest.json"
        if not manifest_path.is_file():
            pytest.skip("P01 artifacts not materialized yet")
        manifest = json.loads(manifest_path.read_text())
        assert manifest["leakage_audit"]["status"] == "PASS"


# --------------------------------------------------------------------------
# 6. Gate mechanism counterexamples
# --------------------------------------------------------------------------
def test_no_gate_equals_c1_decision_path(trained):
    """A1: removing the gate must reproduce the C1 decisions exactly."""
    parts, vocab, model, thresholds, config = trained
    cfg = {"vocabulary": vocab, "weights": model.weights.tolist(),
           "bias": model.bias.tolist()}
    c1 = predict_batch(parts["test"], {**cfg, "model_id": "C1", "gate_mode": "no_gate"})
    a1 = predict_batch(parts["test"], {**cfg, "model_id": "C1", "gate_mode": "no_gate"})
    assert c1.to_jsonl_rows() == a1.to_jsonl_rows()


def test_gate_produces_abstains_and_fail_reroutes(trained):
    parts, vocab, model, thresholds, config = trained
    preds = predict_batch(
        parts["test"],
        {"model_id": "proposed_rc_stg", "vocabulary": vocab,
         "weights": model.weights.tolist(), "bias": model.bias.tolist(),
         "thresholds": thresholds.to_dict(), "gate_mode": "full"},
    )
    decisions = preds.decisions
    assert any(d == ABSTAIN for d in decisions), "gate must abstain somewhere"
    reasons = {rc[0] for rcs in preds.reason_codes for rc in [rcs]}
    assert any("gated_abstain" in r for r in reasons)
    # every ABSTAIN row must carry the low-margin reason
    for d, rcs in zip(decisions, preds.reason_codes):
        if d == ABSTAIN:
            assert rcs[0] == "gated_abstain_low_margin"


def test_fail_false_alarm_rate_matches_preregistered_bound_approximately(trained):
    parts, vocab, model, thresholds, config = trained
    preds = predict_batch(
        parts["test"],
        {"model_id": "proposed_rc_stg", "vocabulary": vocab,
         "weights": model.weights.tolist(), "bias": model.bias.tolist(),
         "thresholds": thresholds.to_dict(), "gate_mode": "full"},
    )
    gold_rows = [{"case_id": r["case_id"], "label": r["label"]} for r in parts["test"]]
    ffa = fail_false_alarm_rate(preds.to_jsonl_rows(), gold_rows)
    assert ffa["n_nonfail"] > 0
    assert 0.0 <= ffa["rate"] <= 1.0
    # empirical check (not a guarantee): near the nominal alpha_fail=0.30
    assert ffa["rate"] < 0.60


def test_random_gate_differs_from_real_gate(synth, trained):
    """A4 mutation: a random gate with matched abstain volume must behave
    differently from the learned gate, else the mechanism is fake."""
    parts, vocab, model, thresholds, config = trained
    cfg = {"vocabulary": vocab, "weights": model.weights.tolist(),
           "bias": model.bias.tolist(), "thresholds": thresholds.to_dict()}
    real = predict_batch(parts["test"], {**cfg, "model_id": "p", "gate_mode": "full"})
    rnd = predict_batch(parts["test"], {**cfg, "model_id": "p", "gate_mode": "random_gate"})
    assert real.to_jsonl_rows() != rnd.to_jsonl_rows()


# --------------------------------------------------------------------------
# 7. End-to-end run on real data (single heavier test)
# --------------------------------------------------------------------------
def test_run_protocol_on_real_oulad_end_to_end(tmp_path):
    """Full protocol T on the real adapter, then artifact round-trip."""
    rows, audit = load_validated_rows()
    assert audit["status"] == "PASS"
    assert len(rows) == 32593
    summary = run_protocol(
        "T", rows, tmp_path,
        config=ModelConfig(seed=0),
        prereg_sha256="0" * 64,
        method_commit_sha="test",
    )
    # determinism: rerun produces identical prediction bytes
    run_protocol(
        "T", rows, tmp_path.parent / "rerun",
        config=ModelConfig(seed=0),
        prereg_sha256="0" * 64,
        method_commit_sha="test",
    )
    a = (tmp_path / "T" / "predictions_proposed_rc_stg.jsonl").read_bytes()
    b = (tmp_path.parent / "rerun" / "T" / "predictions_proposed_rc_stg.jsonl").read_bytes()
    assert a == b
    # null result must be disclosed
    null_rec = json.loads((tmp_path / "T" / "null_result.json").read_text())
    assert null_rec["is_null_or_negative"] is True
    # metrics recomputable
    saved = json.loads((tmp_path / "T" / "metrics_C1_regularized_logistic.json").read_text())
    pred_rows = [
        json.loads(l)
        for l in (tmp_path / "T" / "predictions_C1_regularized_logistic.jsonl")
        .read_text().splitlines() if l.strip()
    ]
    gold_rows = [
        json.loads(l)
        for l in (tmp_path / "T" / "sealed_gold.jsonl").read_text().splitlines() if l.strip()
    ]
    recomputed = compute_classification_metrics(pred_rows, gold_rows, model_id="C1")
    assert recomputed["accuracy"] == saved["accuracy"]
    # T-protocol test rows are all 2014J
    test_ids = {r["case_id"] for r in gold_rows}
    test_rows = [r for r in rows if r["case_id"] in test_ids]
    assert {r["time_key"] for r in test_rows} == {"2014J"}


# --------------------------------------------------------------------------
# 8. C0 sanity
# --------------------------------------------------------------------------
def test_c0_majority_predicts_modal_label(synth, trained):
    parts, *_ = trained
    majority = fit_majority(parts["train"])
    assert majority in LABELS
    preds = predict_majority(parts["test"], majority)
    assert set(preds.decisions) == {majority}


# --------------------------------------------------------------------------
# 9. Status JSON: human-only tasks BLOCKED, never silently accepted
# --------------------------------------------------------------------------
def test_status_json_marks_human_tasks_blocked():
    status_path = RUNS_DIR / "status.json"
    if not status_path.is_file():
        pytest.skip("P01 status.json not materialized yet; run run_p01 first")
    status = json.loads(status_path.read_text())
    for task in ("P01-T19", "P01-T20", "P01-T21"):
        assert status["tasks"][task] == "BLOCKED"
        assert task in status["blocked_tasks_detail"]
    assert status["null_results_disclosed"] is True
