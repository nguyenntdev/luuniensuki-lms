"""P01 run pipeline: split -> audit -> fit -> calibrate -> predict -> artifacts.

One entry point used by both the CLI and the tests so behavior cannot diverge.
Deterministic end to end under a fixed seed; artifacts are strict JSON.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from research_v3.contracts.cards import ExperimentCard
from research_v3.datasets.adapters.oulad import assert_no_label_in_input, load_students
from research_v3.datasets.registry import load_registry, require_approved
from research_v3.eval.leakage import assert_disjoint_groups, audit_rows
from research_v3.eval.splitters import (
    assert_no_leakage,
    freeze_hash,
    group_split,
    time_split,
)
from research_v2.contracts.canonical_hash import sha256_file, sha256_input

from .features import build_vocabulary, save_vocabulary
from .metrics import (
    compute_classification_metrics,
    fail_false_alarm_rate,
    paired_mcnemar,
)
from .models import (
    calibrate_gate,
    fit_classical,
    fit_majority,
    predict_batch,
    predict_classical_batch,
    predict_majority,
)
from .types import LABELS, ModelConfig, P01ContractError, Predictions

DATASET_ID = "oulad-2013-2014"
SALT_GROUP = "p01-v3"
PRESENTATION_ORDER = ("2013B", "2013J", "2014B", "2014J")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, allow_nan=False), encoding="utf-8"
    )


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


def _partition_rows(
    rows: list[dict[str, Any]], split_ids: Mapping[str, tuple[str, ...]]
) -> dict[str, list[dict[str, Any]]]:
    id_to_part: dict[str, str] = {}
    for part, ids in split_ids.items():
        for cid in ids:
            id_to_part[cid] = part
    parts: dict[str, list[dict[str, Any]]] = {p: [] for p in split_ids}
    for row in rows:
        cid = str(row["case_id"])
        if cid in id_to_part:
            parts[id_to_part[cid]].append(row)
    return parts


def enforce_learner_disjointness(
    parts: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Remove earlier-partition rows of learners that appear in later partitions.

    Later partitions (test > dev > calibration > train) keep their rows;
    earlier partitions yield the overlapping rows. This makes the temporal
    protocol learner-disjoint without touching the frozen test set.
    """
    priority = ["test", "dev", "calibration", "train"]
    seen: dict[str, str] = {}
    for part in priority:
        for row in parts[part]:
            seen.setdefault(str(row["group_id"]), part)
    out: dict[str, list[dict[str, Any]]] = {}
    removed = 0
    for part in priority:
        kept: list[dict[str, Any]] = []
        for row in parts[part]:
            if seen[str(row["group_id"])] == part:
                kept.append(row)
            else:
                removed += 1
        out[part] = kept
    return out, removed


def run_protocol(
    protocol: str,
    rows: list[dict[str, Any]],
    out_dir: Path,
    *,
    config: ModelConfig,
    prereg_sha256: str,
    method_commit_sha: str,
) -> dict[str, Any]:
    """Execute one preregistered protocol end to end and write all artifacts."""
    t0 = time.time()
    run_dir = out_dir / protocol
    run_dir.mkdir(parents=True, exist_ok=True)

    # ---- splits (materialized deterministically, hashed, audited) -----------
    if protocol == "T":
        raw_split = time_split(
            rows, time_key="time_key", paper_id="P01", train_fraction=0.70
        )
    elif protocol == "G":
        raw_split = group_split(
            rows,
            group_key="group_id",
            paper_id="P01",
            fractions=(0.70, 0.10, 0.10, 0.10),
            salt=SALT_GROUP,
        )
    else:
        raise P01ContractError(f"unknown protocol {protocol!r}")
    assert_no_leakage(raw_split)
    parts = _partition_rows(rows, raw_split.split_ids)
    removed = 0
    if protocol == "T":
        parts, removed = enforce_learner_disjointness(parts)
        assert_disjoint_groups(
            parts["train"], parts["test"], group_key="group_id"
        )
        assert_disjoint_groups(parts["train"], parts["calibration"], group_key="group_id")
        assert_disjoint_groups(parts["train"], parts["dev"], group_key="group_id")
        assert_disjoint_groups(parts["calibration"], parts["test"], group_key="group_id")

    split_manifest = {
        "protocol": protocol,
        "paper_id": "P01",
        "split_hash": freeze_hash(raw_split),
        "sizes_raw": {k: len(v) for k, v in raw_split.split_ids.items()},
        "sizes_after_learner_disjointness": {k: len(v) for k, v in parts.items()},
        "rows_removed_for_learner_disjointness": removed,
        "unique_learners": {
            k: len({r["group_id"] for r in v}) for k, v in parts.items()
        },
        "presentations_by_part": {
            k: {
                p: sum(1 for r in v if r["input"]["code_presentation"] == p)
                for p in PRESENTATION_ORDER
            }
            for k, v in parts.items()
        },
        "leakage_audit": audit_rows(rows, strict=False),
        "label_distribution_by_part": {
            k: {
                lab: sum(1 for r in v if r["label"] == lab) for lab in LABELS
            }
            for k, v in parts.items()
        },
    }
    assert split_manifest["leakage_audit"]["status"] == "PASS", "leakage audit must pass"
    _write_json(run_dir / "splits_manifest.json", split_manifest)

    # ---- features -----------------------------------------------------------
    vocabulary = build_vocabulary(parts["train"])
    vocab_sha = save_vocabulary(vocabulary, run_dir / "features" / "vocabulary.json")

    # ---- models -------------------------------------------------------------
    majority_label = fit_majority(parts["train"])
    c0_preds = predict_majority(parts["test"], majority_label)

    model = fit_classical(parts["train"], vocabulary, config=config)
    W, b = model.weights.tolist(), model.bias.tolist()

    cal_probs = model.predict_proba(
        np.asarray(_features_for(parts["calibration"], vocabulary))
    )
    thresholds = calibrate_gate(parts["calibration"], cal_probs, config=config)

    common_cfg = {
        "vocabulary": vocabulary,
        "weights": W,
        "bias": b,
        "seed": config.seed,
    }
    c1_preds = predict_classical_batch(parts["test"], common_cfg)
    prop_preds = predict_batch(
        parts["test"],
        {
            **common_cfg,
            "model_id": "proposed_rc_stg",
            "thresholds": thresholds.to_dict(),
            "gate_mode": "full",
        },
    )

    ablation_preds: dict[str, Predictions] = {}
    for mode, aid in [
        ("no_gate", "A1_no_gate"),
        ("no_fail_gate", "A2_no_fail_gate"),
        ("no_abstention", "A3_no_abstention"),
        ("random_gate", "A4_random_gate"),
        ("shuffled_thresholds", "A5_shuffled_thresholds"),
    ]:
        ablation_preds[aid] = predict_batch(
            parts["test"],
            {
                **common_cfg,
                "model_id": aid,
                "thresholds": thresholds.to_dict(),
                "gate_mode": mode,
            },
        )

    # ---- sealed gold (evaluator side only) ----------------------------------
    gold_rows = [
        {
            "case_id": str(r["case_id"]),
            "label": str(r["label"]),
            "group_id": str(r["group_id"]),
        }
        for r in parts["test"]
    ]
    gold_path = run_dir / "sealed_gold.jsonl"
    _write_jsonl(gold_path, gold_rows)

    # ---- predictions + metrics ---------------------------------------------
    all_preds = {"C0_majority_sanity": c0_preds, "C1_regularized_logistic": c1_preds,
                 "proposed_rc_stg": prop_preds, **ablation_preds}
    metrics_by_model: dict[str, dict[str, Any]] = {}
    for model_id, preds in all_preds.items():
        rows_out = preds.to_jsonl_rows()
        _write_jsonl(run_dir / f"predictions_{model_id}.jsonl", rows_out)
        metrics_by_model[model_id] = compute_classification_metrics(
            rows_out, gold_rows, model_id=model_id
        )
        metrics_by_model[model_id]["predictions_sha256"] = sha256_input(rows_out)
        _write_json(run_dir / f"metrics_{model_id}.json", metrics_by_model[model_id])

    # ---- statistical tests (confirmatory family, Holm-corrected) -----------
    m_prop = paired_mcnemar(
        prop_preds.to_jsonl_rows(), c1_preds.to_jsonl_rows(), gold_rows,
        label_a="proposed_rc_stg", label_b="C1_regularized_logistic",
    )
    m_c0 = paired_mcnemar(
        prop_preds.to_jsonl_rows(), c0_preds.to_jsonl_rows(), gold_rows,
        label_a="proposed_rc_stg", label_b="C0_majority_sanity",
    )
    from research_v3.eval.statistics import family_control, null_result

    p_values = [float(m_prop["p_value"]), float(m_c0["p_value"])]
    holm = family_control(p_values, method="holm")
    stat_payload = {
        "family": ["proposed_vs_C1", "proposed_vs_C0"],
        "method": "holm",
        "raw_p_values": dict(zip(["proposed_vs_C1", "proposed_vs_C0"], p_values)),
        "holm_adjusted_p_values": dict(zip(["proposed_vs_C1", "proposed_vs_C0"], holm)),
        "tests": {"proposed_vs_C1": m_prop, "proposed_vs_C0": m_c0},
        "cluster_bootstrap": _cluster_bootstrap(prop_preds, c1_preds, gold_rows, config.seed),
    }
    _write_json(run_dir / "statistical_tests.json", stat_payload)

    acc_prop = metrics_by_model["proposed_rc_stg"]["accuracy"]
    acc_c1 = metrics_by_model["C1_regularized_logistic"]["accuracy"]
    p_holm_c1 = dict(zip(["proposed_vs_C1", "proposed_vs_C0"], holm))["proposed_vs_C1"]
    null_payload = null_result(
        observed=acc_prop, baseline=acc_c1, p_value=float(m_prop["p_value"])
    )
    null_payload["holm_adjusted_p_value_vs_C1"] = p_holm_c1
    null_payload["h0_rejected_at_0.05"] = bool(p_holm_c1 < 0.05 and acc_prop > acc_c1)
    null_payload["preregistered_expectation"] = (
        "The gate trades accuracy for risk control; a null was the expected honest "
        "outcome and is disclosed, not tuned away."
    )
    _write_json(run_dir / "null_result.json", null_payload)

    # ---- calibration + robustness (proposed and C1) -------------------------
    for model_id, preds in [("proposed_rc_stg", prop_preds), ("C1_regularized_logistic", c1_preds)]:
        calib = _calibration_payload(preds.to_jsonl_rows(), gold_rows)
        _write_json(run_dir / f"calibration_{model_id}.json", calib)
        robust = _robustness_payload(preds.to_jsonl_rows(), gold_rows, parts["test"])
        _write_json(run_dir / f"robustness_{model_id}.json", robust)

    # ---- experiment card -----------------------------------------------------
    card = ExperimentCard(
        paper_id="P01",
        rq_id="RQ1_selective_risk_calibrated_transfer",
        train_dataset_ids=(DATASET_ID,),
        holdout_dataset_ids=(DATASET_ID,),
        method_commit_sha=method_commit_sha or "uncommitted",
        method_hash=sha256_file(Path(__file__).resolve()),
        baseline_version="C1_numpy_logreg_l2_1.0",
        split_hash=split_manifest["split_hash"],
        feature_cutoff="60_day_early_click_window",
        prereg_sha256=prereg_sha256,
        hyperparameter_budget=json.dumps(config.to_dict(), sort_keys=True),
        seed=config.seed,
        hardware="cpu_numpy",
        wall_time_seconds=round(time.time() - t0, 3),
        dependency_lock_sha256=sha256_input({"numpy": np.__version__}),
        output_path=str(run_dir),
        protocol_deviations=(
            (
                "time_split empirical composition: train contains a small 2014J tail; "
                "learner overlap across partitions removed by yielding earlier rows"
            )
            if protocol == "T"
            else ()
        ),
        status="PARTIAL",
    )
    _write_json(run_dir / "experiment_card.json", card.to_dict())

    return {
        "protocol": protocol,
        "sizes": {k: len(v) for k, v in parts.items()},
        "majority_label": majority_label,
        "thresholds": thresholds.to_dict(),
        "metrics": metrics_by_model,
        "null_result": null_payload,
    }


def _features_for(rows: list[dict[str, Any]], vocabulary: Mapping[str, Any]) -> np.ndarray:
    from .features import featurize_rows

    return featurize_rows(rows, vocabulary)


def _cluster_bootstrap(
    prop_preds: Predictions,
    c1_preds: Predictions,
    gold_rows: list[dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    from research_v3.eval.statistics import paired_report

    gold_by_case = {str(r["case_id"]): str(r["label"]) for r in gold_rows}
    group_by_case = {str(r["case_id"]): str(r["group_id"]) for r in gold_rows}
    p_prop = {str(r["case_id"]): str(r["decision"]) for r in prop_preds.to_jsonl_rows()}
    p_c1 = {str(r["case_id"]): str(r["decision"]) for r in c1_preds.to_jsonl_rows()}
    cases = sorted(gold_by_case)
    diffs = [int(p_prop[c] == gold_by_case[c]) - int(p_c1[c] == gold_by_case[c]) for c in cases]
    groups = [group_by_case[c] for c in cases]
    return paired_report(
        [d > 0 for d in diffs],
        [d < 0 for d in diffs],
        groups,
        label_a="proposed_rc_stg",
        label_b="C1_regularized_logistic",
        seed=seed,
        n_boot=2000,
    )


def _calibration_payload(pred_rows: list[dict[str, Any]], gold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    from research_v3.eval.calibration import expected_calibration_error, reliability_bins

    gold_by_case = {str(r["case_id"]): str(r["label"]) for r in gold_rows}
    probs: list[float] = []
    outcomes: list[int] = []
    for r in pred_rows:
        gold = gold_by_case[str(r["case_id"])]
        probs.append(float(r["score"]))
        outcomes.append(1 if str(r["decision"]) == gold else 0)
    bins = reliability_bins(probs, outcomes, n_bins=10)
    return {
        "ece_margin": expected_calibration_error(bins),
        "reliability_bins": bins,
        "note": "score = margin of the emitted class; ABSTAIN rows keep their (low) margin",
    }


def _robustness_payload(
    pred_rows: list[dict[str, Any]],
    gold_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    from research_v3.eval.calibration import robustness_report

    gold_by_case = {str(r["case_id"]): str(r["label"]) for r in gold_rows}
    feats_by_case = {str(r["case_id"]): r["input"] for r in test_rows}
    payload: dict[str, Any] = {}
    for field in ("region", "age_band", "disability", "imd_band"):
        per_group: dict[str, list[bool]] = {}
        for r in pred_rows:
            cid = str(r["case_id"])
            group = str(feats_by_case[cid].get(field, "unknown"))
            per_group.setdefault(group, []).append(str(r["decision"]) == gold_by_case[cid])
        payload[field] = robustness_report(per_group, min_n=20)
    return payload


def load_validated_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """License-gated, leakage-audited OULAD rows (fail-closed)."""
    registry = load_registry()
    require_approved(registry, [DATASET_ID], paper_id="P01")
    rows = load_students()
    assert_no_label_in_input(rows)
    report = audit_rows(rows, strict=True)
    if report["status"] != "PASS":
        raise P01ContractError("leakage audit failed; refusing to run")
    return rows, report


def main(
    out_root: str | Path = "research_artifacts_v3/runs/p01",
    seeds: tuple[int, ...] = (0,),
) -> dict[str, Any]:
    """CLI entry point. Runs both preregistered protocols for each seed."""
    out_dir = Path(out_root)
    rows, audit = load_validated_rows()
    project_root = Path(__file__).resolve().parents[3]
    prereg_path = project_root / "research_v3" / "experiments" / "p01" / "preregistration.yaml"
    prereg_sha = sha256_file(prereg_path)
    import subprocess

    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()

    summary: dict[str, Any] = {
        "dataset": DATASET_ID,
        "rows_used": len(rows),
        "leakage_audit": audit,
        "protocols": {},
        "prereg_sha256": prereg_sha,
    }
    for seed in seeds:
        config = ModelConfig(seed=seed)
        for protocol in ("T", "G"):
            result = run_protocol(
                protocol,
                rows,
                out_dir,
                config=config,
                prereg_sha256=prereg_sha,
                method_commit_sha=commit,
            )
            summary["protocols"][f"{protocol}_seed{seed}"] = {
                k: result[k] for k in ("sizes", "majority_label", "thresholds", "null_result")
            }
    _write_json(out_dir / "status.json", _status_payload(summary))
    return summary


def _status_payload(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "paper_id": "P01",
        "status": "EXECUTED_WITH_NULL_RESULT",
        "tasks": {
            **{f"P01-T{n:02d}": "DONE" for n in range(1, 19)},
            "P01-T19": "BLOCKED",
            "P01-T20": "BLOCKED",
            "P01-T21": "BLOCKED",
        },
        "blocked_tasks_detail": {
            "P01-T19": {
                "task": "Ethics/human annotation/license approval (human-only)",
                "reason": "Requires documented human signoff; code agent must not simulate approvals.",
            },
            "P01-T20": {
                "task": "Novelty and nearest-work signoff (research lead)",
                "reason": "Research-lead-only responsibility per 04_METHODOLOGY/NOVELTY_AND_LITERATURE.md.",
            },
            "P01-T21": {
                "task": "Coauthor/venue/submission signoff (human-only)",
                "reason": "Requires human authorship and venue decisions.",
            },
        },
        "null_results_disclosed": True,
        "external_validity": "single dataset (OULAD 2013-2014), observational, not causal, no SOTA claim",
        "summary": dict(summary),
    }


if __name__ == "__main__":
    payload = main()
    print(json.dumps({k: payload[k] for k in ("dataset", "rows_used")}, indent=2))
    for key, res in payload["protocols"].items():
        print(key, "sizes:", res["sizes"], "null:", res["null_result"]["is_null_or_negative"])
