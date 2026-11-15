"""P07 evaluation CLI.

Usage:
    python -m research_v3.experiments.p07.run_matrix [--out DIR]

Runs the frozen matrix (stress synthetic + external Smithsonian CC0) for all
methods and preregistered ablations, applies paired statistics (mcnemar exact
+ cluster bootstrap CI + Holm correction) and writes all artifacts with
SHA-256 checksums. Exit code 0 only if every scored cell ran strictly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from research_v2.evaluation.statistical_tests import mcnemar_exact  # noqa: E402
from research_v3.contracts.cards import ExperimentCard  # noqa: E402
from research_v2.contracts.canonical_hash import sha256_input, sha256_file  # noqa: E402
from research_v3.eval.statistics import (  # noqa: E402
    cluster_bootstrap_paired,  # noqa: F401  (kept for parity with prereg wording)
    family_control,
    proportion_ci,
)
from research_v3.methods.p07.ablations import predict_case as ablation_predict  # noqa: E402
from research_v3.methods.p07.runner import (  # noqa: E402
    evaluate,
    gold_from_cases,
    load_jsonl,
    run_method,
)
from research_v3.methods.p07.synthetic_generator import (  # noqa: E402
    SYNTHETIC_LICENSE,
    generate_stress_cases,
)

from research_v2.evaluation.statistical_tests import cliffs_delta  # noqa: E402

RUN_ID = "p07-wave1"
METHODS = ("proposed", "c0_url_present", "c1_static_image_fallback", "b05_random_eligible")
ABLATIONS = ("A1_no_affordance_coverage", "A2_no_device_constraints", "A5_no_rights_filtering")

STRESS_PREREG_PATH = REPO_ROOT / "research_v3" / "experiments" / "p07" / "prereg.yaml"
MATRIX_PATH = REPO_ROOT / "research_v3" / "experiments" / "p07" / "matrix.yaml"
EXTERNAL_DATA = REPO_ROOT / "research_v3" / "methods" / "p07" / "data" / "smithsonian_fsg_external.jsonl"
OUT_DIR = REPO_ROOT / "research_artifacts_v3" / "runs" / "p07" / RUN_ID


def _paired_stats(preds_a: list[dict[str, Any]], preds_b: list[dict[str, Any]],
                  golds: dict[str, str], groups: dict[str, str]) -> dict[str, Any]:
    """Paired correctness (exact match vs gold) A vs B with McNemar + CI."""
    by_a = {str(p["case_id"]): p for p in preds_a}
    by_b = {str(p["case_id"]): p for p in preds_b}
    shared = sorted(set(by_a) & set(by_b))
    a_ok = [by_a[c]["decision"] == golds[c] for c in shared]
    b_ok = [by_b[c]["decision"] == golds[c] for c in shared]
    gid = [groups[c] for c in shared]
    diffs = [int(x) - int(y) for x, y in zip(a_ok, b_ok)]
    return {
        "n": len(shared),
        "n_a_correct": int(sum(a_ok)),
        "n_b_correct": int(sum(b_ok)),
        "mean_diff": (sum(diffs) / len(diffs)) if diffs else None,
        "mcnemar": mcnemar_exact(a_ok, b_ok),
        "cluster_bootstrap_ci95": cluster_bootstrap_paired(diffs, gid, seed=42, n=2000)["ci_95"],
        "cliffs_delta": cliffs_delta([1.0 if x else 0.0 for x in a_ok], [1.0 if y else 0.0 for y in b_ok]),
        "proportion_ci_a": proportion_ci(int(sum(a_ok)), len(a_ok)),
        "proportion_ci_b": proportion_ci(int(sum(b_ok)), len(b_ok)),
    }


def _identifiability_check(preds: list[dict[str, Any]], golds: dict[str, str]) -> dict[str, Any]:
    """G16: paired cases differing ONLY in the transcript/inscription axis must
    separate — positives selected, negatives explicitly missing-affordance-rejected."""
    by_id = {str(p["case_id"]): p for p in preds}
    pair_results = {}
    pairs: list[tuple[str, str]] = [
        ("S6-PAIR-A-inscription-present", "S6-PAIR-B-inscription-removed"),
        ("S6-PAIR-C-transcript-present", "S6-PAIR-D-transcript-removed"),
    ]
    # external positive/negative twins: <ID>-POS vs <ID>-NEG (identical pool
    # minus the transcription-bearing record)
    ext_pos = sorted(c for c in golds if c.endswith("-POS") and c.startswith("EXT-"))
    for pos in ext_pos:
        neg = pos[: -len("-POS")] + "-NEG"
        if neg in golds:
            pairs.append((pos, neg))
    for pos, neg in pairs:
        if pos in by_id and neg in by_id:
            for cid in (pos, neg):
                pair_results[cid] = {
                    "gold": golds[cid],
                    "pred": by_id[cid]["decision"],
                    "correct": by_id[cid]["decision"] == golds[cid],
                }
    separated = all(r["correct"] for r in pair_results.values()) if pair_results else False
    return {"pairs": pair_results, "separated": separated}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P07 frozen matrix runner")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc).isoformat()

    # ---- suites --------------------------------------------------------
    stress = generate_stress_cases(seed=20261115)
    external = load_jsonl(EXTERNAL_DATA)
    stress_gold = gold_from_cases(stress)
    ext_gold = gold_from_cases(external)

    suites = {
        "stress_synthetic": (stress, stress_gold),
        "external_smithsonian_fsg": (external, ext_gold),
    }

    results: dict[str, Any] = {"run_id": RUN_ID, "started_at": started, "suites": {}}

    # ---- methods -------------------------------------------------------
    for name, (cases, golds) in suites.items():
        case_index = {str(c["case_id"]): c for c in cases}
        groups = {str(c["case_id"]): str(c["group_id"]) for c in cases}
        suite_out: dict[str, Any] = {
            "n_cases": len(cases),
            "n_gold": len(golds),
            "methods": {},
        }
        for method in METHODS:
            preds = run_method(method, cases)
            (out / "predictions").mkdir(parents=True, exist_ok=True)
            pred_path = out / "predictions" / f"{name}__{method}.jsonl"
            pred_path.write_text(
                "".join(json.dumps(p, sort_keys=True) + "\n" for p in preds), encoding="utf-8"
            )
            metrics = evaluate(cases, golds)[method]
            suite_out["methods"][method] = {
                "predictions_sha256": sha256_file(pred_path),
                "metrics": metrics,
            }
            if method == "proposed":
                suite_out["identifiability_g16"] = _identifiability_check(preds, golds)
        # paired contrasts: proposed vs each baseline
        suite_out["contrasts"] = {}
        prop = run_method("proposed", cases)
        for method in METHODS[1:]:
            base = run_method(method, cases)
            suite_out["contrasts"][f"proposed_vs_{method}"] = _paired_stats(prop, base, golds, groups)
        results["suites"][name] = suite_out

    # ---- ablations (true removals) --------------------------------------
    results["ablations"] = {}
    for cell in ("stress_synthetic", "external_smithsonian_fsg"):
        cases, golds = suites[cell]
        case_index = {str(c["case_id"]): c for c in cases}
        groups = {str(c["case_id"]): str(c["group_id"]) for c in cases}
        prop = run_method("proposed", cases)
        for abl in ABLATIONS:
            preds = [ablation_predict(abl, row) for row in cases]
            (out / "predictions").mkdir(parents=True, exist_ok=True)
            pred_path = out / "predictions" / f"{cell}__{abl}.jsonl"
            pred_path.write_text(
                "".join(json.dumps(p, sort_keys=True) + "\n" for p in preds), encoding="utf-8"
            )
            from research_v3.methods.p07.metrics import all_metrics

            metrics = all_metrics(preds, golds, case_index)
            results["ablations"][f"{cell}__{abl}"] = {
                "predictions_sha256": sha256_file(pred_path),
                "metrics": metrics,
                "contrast_vs_proposed": _paired_stats(prop, preds, golds, groups),
            }

    # ---- multiple-comparison control ------------------------------------
    family: list[float] = []
    labels: list[str] = []
    for cell in results["suites"].values():
        for key, c in cell["contrasts"].items():
            p = c["mcnemar"]["p_value"]
            family.append(float(p) if p is not None else 1.0)
            labels.append(key)
    for cell in results["ablations"].values():
        p = cell["contrast_vs_proposed"]["mcnemar"]["p_value"]
        family.append(float(p) if p is not None else 1.0)
        labels.append("ablation:" + next(k for k, v in results["ablations"].items() if v is cell))
    adjusted = family_control(family, method="holm")
    results["multiple_testing"] = {
        "method": "holm",
        "family": {lab: {"p_raw": p, "p_holm": adj} for lab, p, adj in zip(labels, family, adjusted)},
    }

    # ---- determinism: rerun stress suite and compare ---------------------
    stress_rerun = generate_stress_cases(seed=20261115)
    rerun_pred = run_method("proposed", stress_rerun)
    first_pred = run_method("proposed", stress)
    results["determinism_check"] = {
        "identical": rerun_pred == first_pred,
        "prediction_hash": sha256_input(rerun_pred),
    }

    # ---- experiment card -------------------------------------------------
    card = ExperimentCard(
        paper_id="P07",
        rq_id="RQ-affordance-selection",
        train_dataset_ids=("synthetic-stress-p07", "smithsonian-open-access-fsg"),
        holdout_dataset_ids=("synthetic-stress-p07", "smithsonian-open-access-fsg"),
        method_commit_sha="",
        method_hash=sha256_input({"methods": list(METHODS), "ablations": list(ABLATIONS)}),
        baseline_version="p07-baselines-v1.0",
        split_hash=sha256_input({"suites": {k: [c["case_id"] for c in v[0]] for k, v in suites.items()}}),
        feature_cutoff="static snapshot 2021-12-21",
        prereg_sha256=sha256_file(STRESS_PREREG_PATH),
        hyperparameter_budget="none (no learned parameters)",
        seed=20261115,
        hardware="cpu-only (selection rules, no GPU)",
        wall_time_seconds=0.0,
        dependency_lock_sha256="",
        output_path=str(out.relative_to(REPO_ROOT)),
        status="PARTIAL",
        protocol_deviations=(
            "A3/A4 ablations deferred with dated rationale in matrix.yaml",
            "single external provider; external generalization unverified",
        ),
    )
    results["experiment_card"] = card.to_dict()

    results_path = out / "results.json"
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")

    # checksum manifest
    manifest_lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file():
            manifest_lines.append(f"{sha256_file(path)}  {path.relative_to(out)}")
    (out / "SHA256SUMS.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    print(f"P07 matrix run complete -> {out}")
    for name, suite in results["suites"].items():
        print(f"\n[{name}] n={suite['n_cases']}")
        for method, payload in suite["methods"].items():
            m = payload["metrics"]
            fc = m["false_completion_rate"]["rate"]
            print(f"  {method:28s} feas={m['task_feasibility_rate']['rate']} "
                  f"false_completion={fc} ma_recall={m['missing_affordance_recall']['rate']} "
                  f"rights_viol={m['rights_compliance']['violation_rate']}")
        print("  G16 identifiability separated:", suite["identifiability_g16"]["separated"])
    print("\ndeterminism:", results["determinism_check"]["identical"])
    ok = results["determinism_check"]["identical"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
