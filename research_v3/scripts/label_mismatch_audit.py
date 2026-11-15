"""V3-G14: native-label vs prereg-endpoint mismatch audit.

Reconciles three vocabularies per study WITHOUT relabeling anything:

1. the preregistration endpoint vocabulary (research_v2/experiments/<ln>/
   prereg.yaml: primary_metric + decision_space), and
2. the native frozen-gold label space (research_v2/contracts/label_space.py:
   NATIVE_DECISIONS_BY_STUDY and the gold files themselves), and
3. the shared contract space (DECISIONS_BY_STUDY).

The audit REPORTS divergences (documented in the V2 preregs themselves, e.g.
LN-01/LN-09) and exits nonzero when a divergence is UNDOCUMENTED — i.e. the
prereg does not declare a ``label_space_divergence`` note while its
decision_space disagrees with the native gold vocabulary. Frozen gold is never
rewritten by this script.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v2.contracts.label_space import DECISIONS_BY_STUDY, NATIVE_DECISIONS_BY_STUDY
from research_v3.scripts._paths import RESEARCH_V2_ROOT

EXPERIMENTS_DIR = RESEARCH_V2_ROOT / "experiments"
STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]

EXIT_OK = 0
EXIT_UNDOCUMENTED_MISMATCH = 16
EXIT_CONFIG_ERROR = 7


class LabelMismatchError(RuntimeError):
    """Raised when the audit inputs cannot be read."""


def load_prereg(study_id: str, experiments_dir: Path = EXPERIMENTS_DIR) -> dict | None:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise LabelMismatchError("PyYAML is required") from exc
    slug = study_id.lower().replace("-", "")
    path = experiments_dir / slug / "prereg.yaml"
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_gold_vocabulary(
    study_id: str, data_dir: Path = RESEARCH_V2_ROOT / "data"
) -> set[str] | None:
    gold = data_dir / study_id.lower().replace("-", "") / "t3_gold.jsonl"
    if not gold.is_file():
        return None
    labels: set[str] = set()
    with gold.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            decision = row.get("expected_decision")
            if decision:
                labels.add(str(decision))
    return labels or None


def audit_study(study_id: str, *, experiments_dir: Path = EXPERIMENTS_DIR) -> dict:
    """One study's reconciliation report (pure)."""
    prereg = load_prereg(study_id, experiments_dir)
    native_declared = set(NATIVE_DECISIONS_BY_STUDY.get(study_id, set()))
    contract_declared = set(DECISIONS_BY_STUDY.get(study_id, set()))
    gold_observed = load_gold_vocabulary(study_id)

    prereg_space: set[str] = set()
    if prereg:
        ds = prereg.get("decision_space") or []
        prereg_space = {str(x) for x in ds}
    divergence_note = bool((prereg or {}).get("label_space_divergence"))

    report: dict = {
        "study_id": study_id,
        "prereg_present": prereg is not None,
        "primary_metric": (prereg or {}).get("primary_metric"),
        "prereg_decision_space": sorted(prereg_space),
        "contract_space_declared": sorted(contract_declared),
        "native_space_declared": sorted(native_declared),
        "gold_observed": sorted(gold_observed) if gold_observed is not None else None,
        "label_space_divergence_documented": divergence_note,
        "mismatches": [],
        "status": "OK",
    }

    # 1. prereg decision_space vs native gold vocabulary
    if gold_observed is not None and prereg_space and prereg_space != gold_observed:
        extra = sorted(prereg_space - gold_observed)
        missing = sorted(gold_observed - prereg_space)
        report["mismatches"].append(
            {
                "kind": "prereg_vs_gold",
                "prereg_only_labels": extra,
                "gold_only_labels": missing,
                "documented": divergence_note,
            }
        )
    # 2. declared native space vs actual gold file (vocabulary drift)
    if gold_observed is not None and native_declared and native_declared != gold_observed:
        report["mismatches"].append(
            {
                "kind": "declared_native_vs_gold",
                "declared_only": sorted(native_declared - gold_observed),
                "gold_only": sorted(gold_observed - native_declared),
                "documented": divergence_note,
            }
        )
    # 3. contract space vs prereg space (forward-looking vocabulary divergence)
    if prereg_space and contract_declared and not (prereg_space & contract_declared):
        report["mismatches"].append(
            {
                "kind": "contract_vs_prereg_disjoint",
                "contract_only": sorted(contract_declared - prereg_space),
                "prereg_only": sorted(prereg_space - contract_declared),
                "documented": divergence_note,
            }
        )

    undocumented = [m for m in report["mismatches"] if not m.get("documented")]
    if mismatches := report["mismatches"]:
        report["status"] = "DOCUMENTED_DIVERGENCE" if not undocumented else "UNDOCUMENTED_MISMATCH"
    return report


def run_audit(study_ids: list[str], *, experiments_dir: Path = EXPERIMENTS_DIR) -> list[dict]:
    return [audit_study(s, experiments_dir=experiments_dir) for s in study_ids]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.label_mismatch_audit",
        description=(
            "Reconcile native label vocabularies against prereg endpoints and "
            "report mismatches — never silently relabel frozen gold (V3-G14)."
        ),
    )
    parser.add_argument("--study", action="append", default=[], help="Limit to specific studies (repeatable)")
    parser.add_argument("--all", action="store_true", help="Audit LN-01..LN-10")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args(argv)

    if args.all or not args.study:
        studies = args.study or STUDY_IDS
    else:
        studies = args.study
        unknown = [s for s in studies if s not in STUDY_IDS]
        if unknown:
            print(f"FAIL label_mismatch_audit: unknown study id(s) {unknown}", file=sys.stderr)
            return EXIT_CONFIG_ERROR

    try:
        reports = run_audit(studies)
    except LabelMismatchError as exc:
        print(f"FAIL label_mismatch_audit: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    undocumented = [r for r in reports if r["status"] == "UNDOCUMENTED_MISMATCH"]
    documented = [r for r in reports if r["status"] == "DOCUMENTED_DIVERGENCE"]
    for r in reports:
        if r["mismatches"]:
            print(
                f"{r['study_id']}: {r['status']} — {len(r['mismatches'])} mismatch(es); "
                f"prereg={r['prereg_decision_space']} gold={r['gold_observed']}"
            )
        else:
            print(f"{r['study_id']}: OK")
    if args.json:
        import json as _json

        print(_json.dumps(reports, ensure_ascii=False, indent=2))

    if undocumented:
        print(
            f"FAIL label_mismatch_audit: {len(undocumented)} study(ies) with UNDOCUMENTED "
            "label mismatch — reconcile in the prereg; do NOT relabel frozen gold.",
            file=sys.stderr,
        )
        return EXIT_UNDOCUMENTED_MISMATCH
    if documented:
        print(
            f"OK label_mismatch_audit: {len(documented)} documented divergence(s) reported "
            "(frozen gold untouched)."
        )
    else:
        print("OK label_mismatch_audit: all vocabularies aligned.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
