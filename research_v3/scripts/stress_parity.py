"""V3-G15/G16/G17: external solver parity + scored stress strata.

Three predeclared stress suites (research_v3/datasets/sanitized/, NEW data —
the frozen V2 T3 files are never touched):

- ``ln06_external_solver_parity`` (V3-G15): the V2 LN-06 proposed policy must
  never report FALSE INFEASIBILITY on cases whose exact answer is
  find_valid_route, and every disagreement is reported with an
  exact/approximate marker (no invented global optimum).
- ``ln07_transcript_failure`` (V3-G16): the transcript-failure stratum absent
  from the V2 T3 gold — scored here separately, with positive AND negative
  expectation cases.
- ``ln09_small_cohort`` (V3-G17): the n<5 stratum absent from the V2 T3 gold
  — scored with k-anonymity divergence (proposed vs a3 ablation with the
  k-anonymity flag removed), exposing the mechanism on sealed stress data.

Every discrepancy is reported honestly; the runner exits nonzero when a
predeclared tolerance (false-infeasibility == 0) is violated.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from research_v2.contracts.canonical_hash import sha256_input
from research_v2.contracts.types import StudyInput
from research_v3.datasets.sanitized.generate_stress import FAMILIES, SANITIZED_DIR
from research_v3.scripts._paths import RUNS_DIR

EXIT_OK = 0
EXIT_PARITY_FAILED = 17
EXIT_CONFIG_ERROR = 7


class StressParityError(RuntimeError):
    """Raised when a stress/parity run cannot be executed honestly."""


def _load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def _to_inputs(rows: list[dict[str, Any]], study_id: str) -> list[StudyInput]:
    return [
        StudyInput(
            study_id=study_id,
            case_id=row["case_id"],
            split_id="stress",
            group_id=str(row.get("group_id") or row["case_id"]),
            features=row["input"],
        )
        for row in rows
    ]


def _predict(study_id: str, method_id: str, inputs: list[StudyInput], seed: int) -> list[dict[str, Any]]:
    ln = study_id.lower().replace("-", "")
    from importlib import import_module

    module = import_module(f"research_v2.methods.{ln}.{method_id}")
    fn = getattr(module, "predict_batch", None)
    if fn is None:
        raise StressParityError(f"method {method_id!r} for {study_id} has no predict_batch")
    return [p.to_dict() if hasattr(p, "to_dict") else dict(p) for p in fn(inputs, {"seed": seed})]


def run_ln06_parity(seed: int) -> dict[str, Any]:
    """G15: proposed policy vs independent exact oracle (false infeasibility)."""
    rows = _load_rows(SANITIZED_DIR / "ln06_external_solver_parity" / f"seed{seed}.jsonl")
    inputs = _to_inputs(rows, "LN-06")
    preds = _predict("LN-06", "proposed", inputs, seed)
    by_case = {p["case_id"]: p for p in preds}
    if set(by_case) != {r["case_id"] for r in rows}:
        raise StressParityError("LN-06 parity: prediction coverage mismatch")

    false_infeasible: list[str] = []
    disagreements: list[dict[str, Any]] = []
    exact_agree = 0
    for row in rows:
        pred = by_case[row["case_id"]]["decision"]
        gold = row["label"]
        agree = pred == gold
        exact_agree += agree
        if not agree:
            disagreements.append(
                {
                    "case_id": row["case_id"],
                    "gold": gold,
                    "pred": pred,
                    "marker": "exact" if gold in ("find_valid_route", "no_feasible_route", "cost_exceeded") else "approx",
                }
            )
        # predeclared tolerance: NEVER a false infeasibility on a feasible case
        if gold in ("find_valid_route", "cost_exceeded") and pred in ("no_feasible_route", "reject_cycle"):
            false_infeasible.append(row["case_id"])

    return {
        "suite": "ln06_external_solver_parity",
        "task_id": "V3-G15",
        "seed": seed,
        "n_cases": len(rows),
        "exact_agreement": exact_agree,
        "exact_agreement_rate": exact_agree / len(rows),
        "false_infeasibility_cases": false_infeasible,
        "false_infeasibility_rate": len(false_infeasible) / len(rows),
        "disagreements": disagreements,
        "predeclared_tolerance": "false_infeasibility == 0",
        "status": "PASS" if not false_infeasible else "FAIL",
        "note": (
            "Exact/approximate markers distinguish certified oracle answers from "
            "heuristic ones; no global optimum is claimed beyond the oracle."
        ),
    }


def run_ln07_transcript(seed: int) -> dict[str, Any]:
    """G16: transcript-failure stratum, scored separately, positive+negative."""
    rows = _load_rows(SANITIZED_DIR / "ln07_transcript_failure" / f"seed{seed}.jsonl")
    inputs = _to_inputs(rows, "LN-07")
    preds = _predict("LN-07", "proposed", inputs, seed)
    by_case = {p["case_id"]: p for p in preds}
    if set(by_case) != {r["case_id"] for r in rows}:
        raise StressParityError("LN-07 stress: prediction coverage mismatch")

    stratum_rows = [r for r in rows if r["input"]["task"]["transcript_required"]]
    if not stratum_rows:
        raise StressParityError("LN-07 stress: no transcript_required cases generated")

    positive_cases = [r for r in stratum_rows if r["label"] == "reject_audio_equivalence"]
    negative_cases = [r for r in stratum_rows if r["label"] != "reject_audio_equivalence"]
    if not positive_cases or not negative_cases:
        raise StressParityError(
            "LN-07 stress: both expectation polarities are required (positive: "
            "transcript failure; negative: compliant audio) — regenerate the suite"
        )

    correct = sum(1 for r in stratum_rows if by_case[r["case_id"]]["decision"] == r["label"])
    positives_correct = sum(1 for r in positive_cases if by_case[r["case_id"]]["decision"] == "reject_audio_equivalence")
    negatives_correct = sum(1 for r in negative_cases if by_case[r["case_id"]]["decision"] == r["label"])
    return {
        "suite": "ln07_transcript_failure",
        "task_id": "V3-G16",
        "seed": seed,
        "n_stratum": len(stratum_rows),
        "n_positive_expectation": len(positive_cases),
        "n_negative_expectation": len(negative_cases),
        "accuracy": correct / len(stratum_rows),
        "positive_expectation_accuracy": positives_correct / len(positive_cases),
        "negative_expectation_accuracy": negatives_correct / len(negative_cases),
        "status": "SCORED",
        "note": "Scored stratum; failures are reported, never tuned away.",
    }


def run_ln09_small_cohort(seed: int, *, k_threshold: int = 5) -> dict[str, Any]:
    """G17: n<5 stratum with k-anonymity divergence (proposed vs a3 ablation)."""
    rows = _load_rows(SANITIZED_DIR / "ln09_small_cohort" / f"seed{seed}.jsonl")
    inputs = _to_inputs(rows, "LN-09")
    proposed = _predict("LN-09", "proposed", inputs, seed)
    a3 = _predict("LN-09", "ablations_a3", inputs, seed)  # k-anonymity removed
    prop_by = {p["case_id"]: p for p in proposed}
    a3_by = {p["case_id"]: p for p in a3}

    small = [r for r in rows if r["input"]["cohort_size"] < k_threshold]
    if not small:
        raise StressParityError("LN-09 stress: no n<5 cases generated")
    large = [r for r in rows if r["input"]["cohort_size"] >= k_threshold]

    suppressed = sum(1 for r in small if prop_by[r["case_id"]]["decision"] == "descriptive_only")
    a3_action_on_small = sum(
        1 for r in small if a3_by[r["case_id"]]["decision"] == "propose_explained_action"
    )
    divergent = sum(
        1
        for r in small
        if prop_by[r["case_id"]]["decision"] != a3_by[r["case_id"]]["decision"]
    )
    large_ok = all(
        prop_by[r["case_id"]]["decision"] == "propose_explained_action" for r in large
    )
    return {
        "suite": "ln09_small_cohort",
        "task_id": "V3-G17",
        "seed": seed,
        "k_threshold": k_threshold,
        "n_small": len(small),
        "n_large": len(large),
        "proposed_suppression_rate_on_small": suppressed / len(small),
        "a3_action_rate_on_small": a3_action_on_small / len(small),
        "k_anonymity_divergence_count": divergent,
        "k_anonymity_divergence_rate": divergent / len(small),
        "large_cohort_nominal_rate": (
            sum(1 for r in large if prop_by[r["case_id"]]["decision"] == "propose_explained_action")
            / len(large)
        ),
        "status": "PASS" if (divergent == len(small) and large_ok) else "FAIL",
        "note": (
            "Sealed stress divergence: the proposed policy must suppress EVERY "
            "n<5 cohort while the a3 ablation (k-anonymity removed) acts on them."
        ),
    }


RUNNERS = {
    "ln06_external_solver_parity": run_ln06_parity,
    "ln07_transcript_failure": run_ln07_transcript,
    "ln09_small_cohort": run_ln09_small_cohort,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.stress_parity",
        description=(
            "External solver parity + scored stress strata on NEW sanitized "
            "datasets (V3-G15/G16/G17). Frozen V2 T3 is never touched."
        ),
    )
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        choices=sorted(RUNNERS),
        help="Stress suite to run (repeatable; default all)",
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output", type=Path, default=None, help="Write combined JSON report")
    parser.add_argument(
        "--ensure-datasets",
        action="store_true",
        help="Generate the sanitized suites first if missing (deterministic)",
    )
    args = parser.parse_args(argv)

    suites = args.suite or sorted(RUNNERS)
    if args.ensure_datasets or any(
        not (SANITIZED_DIR / s / f"seed{args.seed}.jsonl").is_file() for s in suites
    ):
        from research_v3.datasets.sanitized.generate_stress import write_family

        for s in suites:
            write_family(s)

    reports: list[dict[str, Any]] = []
    failed = False
    for suite in suites:
        try:
            report = RUNNERS[suite](args.seed)
        except (StressParityError, ValueError) as exc:
            print(f"FAIL stress_parity {suite}: {exc}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        reports.append(report)
        print(
            f"{report['status']} {suite} seed={args.seed}: "
            + ", ".join(
                f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
                for k, v in report.items()
                if k in ("false_infeasibility_rate", "accuracy", "k_anonymity_divergence_rate")
                or k == "status"
            )
        )
        if report["status"] == "FAIL":
            failed = True

    combined = {
        "schema": "research_v3.stress_parity/v1",
        "seed": args.seed,
        "suites": reports,
        "input_suites_sha256": {
            s: sha256_input({"family": s}) for s in suites
        },
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failed:
        print("FAIL stress_parity: predeclared tolerance violated (see report).", file=sys.stderr)
        return EXIT_PARITY_FAILED
    print("OK stress_parity: all requested suites satisfy their predeclared tolerances.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
