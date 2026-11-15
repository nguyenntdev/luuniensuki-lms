"""V3-G02: verify that every dataset required by a paper is APPROVED.

Loads the dataset registry (research_v3/datasets/registry.yaml) and the
per-paper requirement map (research_v3/config/papers/paper_datasets.yaml),
prints a per-status summary, and exits NONZERO when any paper requires a
dataset that is not APPROVED (fail-closed). A public URL is not a license:
only APPROVED cards with captured license-text hashes may back a primary
claim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v3.datasets.registry import load_registry, summary
from research_v3.scripts._paths import PAPER_CONFIG_DIR

PAPER_DATASETS_YAML = PAPER_CONFIG_DIR / "paper_datasets.yaml"

EXIT_OK = 0
EXIT_NOT_APPROVED = 6
EXIT_CONFIG_ERROR = 7


class LicenseVerifyError(RuntimeError):
    """Raised when the paper->dataset configuration itself is unusable."""


def load_paper_requirements(path: Path | None = None) -> dict[str, list[str]]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise LicenseVerifyError("PyYAML is required to read the paper requirements") from exc
    target = Path(path or PAPER_DATASETS_YAML)
    if not target.is_file():
        raise LicenseVerifyError(f"paper requirements file missing: {target}")
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    requirements: dict[str, list[str]] = {}
    for paper_id, datasets in raw.items():
        if not str(paper_id).startswith("P"):
            raise LicenseVerifyError(f"invalid paper key {paper_id!r} in {target}")
        if datasets is None:
            datasets = []
        if not isinstance(datasets, list) or not all(isinstance(d, str) for d in datasets):
            raise LicenseVerifyError(f"{paper_id}: dataset list must be strings")
        requirements[str(paper_id)] = list(datasets)
    return requirements


def verify(
    requirements: dict[str, list[str]],
    registry_path: Path | None = None,
) -> tuple[bool, dict]:
    """Return (all_ok, report). all_ok is False when ANY required dataset is not APPROVED."""
    cards = load_registry(registry_path)
    by_id = {c.dataset_id: c for c in cards}
    report: dict = {
        "registry_summary": summary(cards),
        "papers": {},
        "violations": [],
        "unknown_dataset_ids": [],
    }
    all_ok = True
    for paper_id in sorted(requirements):
        paper_report: dict = {"required": [], "statuses": {}, "ok": True}
        for ds_id in requirements[paper_id]:
            card = by_id.get(ds_id)
            paper_report["required"].append(ds_id)
            if card is None:
                paper_report["statuses"][ds_id] = "NOT_REGISTERED"
                paper_report["ok"] = False
                report["violations"].append(
                    {"paper_id": paper_id, "dataset_id": ds_id, "reason": "not registered in registry.yaml"}
                )
                if ds_id not in report["unknown_dataset_ids"]:
                    report["unknown_dataset_ids"].append(ds_id)
                continue
            paper_report["statuses"][ds_id] = card.status
            if card.status != "APPROVED":
                paper_report["ok"] = False
                report["violations"].append(
                    {
                        "paper_id": paper_id,
                        "dataset_id": ds_id,
                        "reason": f"status={card.status}: {card.blocked_reason or 'no blocked_reason recorded'}",
                    }
                )
        report["papers"][paper_id] = paper_report
        if not paper_report["ok"]:
            all_ok = False
    report["all_papers_licensed"] = all_ok
    return all_ok, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.verify_licenses",
        description=(
            "Fail-closed license gate: every dataset a paper requires must be "
            "APPROVED in the registry (V3-G02). Exits nonzero otherwise."
        ),
    )
    parser.add_argument("--all", action="store_true", help="Verify all papers in the requirements map")
    parser.add_argument("--paper", action="append", default=[], help="Verify a specific paper (repeatable)")
    parser.add_argument("--strict", action="store_true", help="Nonzero exit on any violation (default behavior)")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help=(
            "Advisory reporting mode: print the full per-paper BLOCKED/violation "
            "list but exit 0. Configuration errors (exit 7) still fail. The "
            "STRICT gate is the invocation WITHOUT this flag; in CI the strict "
            "gate runs per fully-approved paper plus a hard scan that no run "
            "artifact binds a BLOCKED dataset."
        ),
    )
    parser.add_argument("--registry", type=Path, default=None, help="Alternate registry.yaml path")
    parser.add_argument(
        "--requirements",
        type=Path,
        default=PAPER_DATASETS_YAML,
        help="Alternate paper->dataset requirements YAML",
    )
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    args = parser.parse_args(argv)

    try:
        requirements = load_paper_requirements(args.requirements)
    except LicenseVerifyError as exc:
        print(f"FAIL verify_licenses: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    if args.paper:
        unknown = [p for p in args.paper if p not in requirements]
        if unknown:
            print(f"FAIL verify_licenses: unknown paper(s) {unknown}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        requirements = {p: requirements[p] for p in args.paper}
    elif not args.all:
        parser.print_help()
        print("\nERROR: pass --all or --paper Pxx", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    all_ok, report = verify(requirements, args.registry)

    reg = report["registry_summary"]
    print(f"Registry: {reg['total']} cards, by status {reg['by_status']}")
    for paper_id in sorted(report["papers"]):
        p = report["papers"][paper_id]
        statuses = ", ".join(f"{d}={s}" for d, s in p["statuses"].items()) or "(none required)"
        print(f"  {paper_id}: {'OK' if p['ok'] else 'BLOCKED'} | {statuses}")
    for v in report["violations"]:
        print(f"VIOLATION {v['paper_id']}: {v['dataset_id']} — {v['reason']}", file=sys.stderr)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if not all_ok:
        print(
            f"FAIL verify_licenses: {len(report['violations'])} dataset(s) required by papers "
            "are not APPROVED — primary claims stay BLOCKED (fail-closed).",
            file=sys.stderr,
        )
        if not args.report_only:
            return EXIT_NOT_APPROVED
        print(
            "ADVISORY (--report-only): violations listed above are recorded but do NOT "
            "fail this step. CI enforces the strict policy separately: per-paper "
            "verification for fully-approved papers plus a hard scan that no committed "
            "run artifact binds a non-APPROVED dataset as a primary result basis.",
        )
        return EXIT_OK
    print("OK verify_licenses: every required dataset is APPROVED.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
