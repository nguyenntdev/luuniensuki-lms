"""V3-G07: paired evaluation from SAVED predictions + gold.

Consumes two prediction JSONL files (proposed vs baseline — each row needs
``case_id`` and ``decision``) and one gold JSONL (``case_id`` +
``expected_decision``), aligns them by case_id (fail-closed on duplicates,
missing or extra ids), and emits:

- ``paired_report``    : exact McNemar + cluster bootstrap CI + effect size
- ``family_control``   : Holm/BH adjustment across the family of p-values given
- ``null_result``      : explicit null/negative-result record — negatives are
  PRESERVED, never tuned away or dropped

No metric is invented: every number derives from the comparison of the given
files. Exit nonzero when the files cannot be aligned or statistics fail.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v3.eval.statistics import family_control, null_result, paired_report
from research_v3.scripts._paths import RUNS_DIR

EXIT_OK = 0
EXIT_EVALUATION_FAILED = 13


class EvaluationError(ValueError):
    """Raised when predictions/gold cannot be aligned or are malformed."""


def load_jsonl(path: Path, id_field: str, value_field: str) -> dict[str, str]:
    if not path.is_file():
        raise EvaluationError(f"file not found: {path}")
    values: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            cid = row.get(id_field)
            value = row.get(value_field)
            if cid is None or value is None:
                raise EvaluationError(f"{path}:{lineno}: missing {id_field!r} or {value_field!r}")
            cid = str(cid)
            if cid in values:
                raise EvaluationError(f"{path}:{lineno}: duplicate case_id {cid!r}")
            values[cid] = str(value)
    if not values:
        raise EvaluationError(f"{path}: no rows")
    return values


def align(
    gold: dict[str, str],
    pred_a: dict[str, str],
    pred_b: dict[str, str],
) -> tuple[list[str], list[bool], list[bool], list[str]]:
    """Two-sided, fail-closed alignment: missing/extra ids are errors."""
    ids = sorted(gold)
    missing_a = [c for c in ids if c not in pred_a]
    missing_b = [c for c in ids if c not in pred_b]
    extra_a = sorted(set(pred_a) - set(gold))
    extra_b = sorted(set(pred_b) - set(gold))
    problems = []
    if missing_a:
        problems.append(f"proposed missing {len(missing_a)} case_id(s), e.g. {missing_a[:3]}")
    if missing_b:
        problems.append(f"baseline missing {len(missing_b)} case_id(s), e.g. {missing_b[:3]}")
    if extra_a:
        problems.append(f"proposed has {len(extra_a)} extra case_id(s), e.g. {extra_a[:3]}")
    if extra_b:
        problems.append(f"baseline has {len(extra_b)} extra case_id(s), e.g. {extra_b[:3]}")
    if problems:
        raise EvaluationError("coverage mismatch: " + "; ".join(problems))
    case_ids = sorted(set(gold) & set(pred_a) & set(pred_b))
    a_correct = [pred_a[c] == gold[c] for c in case_ids]
    b_correct = [pred_b[c] == gold[c] for c in case_ids]
    groups = [c.rsplit("-", 1)[0] for c in case_ids]
    return case_ids, a_correct, b_correct, groups


def run_evaluation(
    *,
    gold: dict[str, str],
    pred_a: dict[str, str],
    pred_b: dict[str, str],
    label_a: str,
    label_b: str,
    seed: int,
    extra_p_values: list[float] | None = None,
) -> dict:
    case_ids, a_correct, b_correct, groups = align(gold, pred_a, pred_b)
    report = paired_report(a_correct, b_correct, groups, label_a=label_a, label_b=label_b, seed=seed)
    mc_p = (report.get("mcnemar") or {}).get("p_value")
    p_values = ([mc_p] if mc_p is not None else []) + list(extra_p_values or [])
    report["family_control"] = (
        {
            "method": "holm",
            "p_values_input": p_values,
            "p_values_adjusted": family_control(p_values, method="holm"),
        }
        if p_values
        else None
    )
    acc_a = sum(a_correct) / len(a_correct)
    acc_b = sum(b_correct) / len(b_correct)
    report["null_result"] = null_result(
        observed=acc_a,
        baseline=acc_b,
        p_value=mc_p,
    )
    report["case_count"] = len(case_ids)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.evaluate",
        description=(
            "Paired evaluation of two saved prediction files against gold; "
            "emits paired_report + family_control + null_result (V3-G07). "
            "Negative results are preserved, never dropped."
        ),
    )
    parser.add_argument("--gold", type=Path, required=True, help="Gold JSONL (case_id, expected_decision)")
    parser.add_argument("--proposed", type=Path, required=True, help="Proposed predictions JSONL (case_id, decision)")
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline predictions JSONL (case_id, decision)")
    parser.add_argument("--label-a", default="proposed")
    parser.add_argument("--label-b", default="baseline")
    parser.add_argument("--seed", type=int, default=42, help="Cluster-bootstrap seed")
    parser.add_argument("--output", type=Path, default=None, help="Write the JSON report here")
    args = parser.parse_args(argv)

    try:
        gold = load_jsonl(args.gold, "case_id", "expected_decision")
        pred_a = load_jsonl(args.proposed, "case_id", "decision")
        pred_b = load_jsonl(args.baseline, "case_id", "decision")
        report = run_evaluation(
            gold=gold,
            pred_a=pred_a,
            pred_b=pred_b,
            label_a=args.label_a,
            label_b=args.label_b,
            seed=args.seed,
        )
    except EvaluationError as exc:
        print(f"FAIL evaluate: {exc}", file=sys.stderr)
        return EXIT_EVALUATION_FAILED

    is_null = report["null_result"]["is_null_or_negative"]
    summary = (
        f"n={report['n']} mean_diff={report['mean_diff']:.4f} "
        f"mcnemar_p={report['mcnemar']['p_value'] if report['mcnemar'] else None} "
        f"null_or_negative={is_null}"
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        summary += f" -> {args.output}"
    prefix = "RESULT (null/negative preserved)" if is_null else "RESULT"
    print(f"{prefix} evaluate: {summary}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
