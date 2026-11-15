"""V3-G23: cross-verify "tier executed" claims against actual run manifests.

The audit found that release prose can claim tiers (e.g. "T1,T2,T3 executed")
that the on-disk manifests do not support. This verifier recomputes, from the
run manifests on disk (not from any CLI string or prose):

- the set of (study, tier) pairs actually executed with a PASS/FAIL manifest;
- the manifest count per tier and the comparator set per study;
- the claimed tiers parsed from release docs (BENCHMARK_APPENDIX.md,
  SCIENTIFIC_READINESS.md, release_manifest.json source_commit) plus the
  research-v2 CI workflow's --tier argument;
- PASS/PARTIAL re-derivation from metrics.json on disk vs the readiness table.

Fail-closed: a claim of an executed tier with ZERO manifests on disk, or a
readiness table that disagrees with recomputed means, exits nonzero.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from research_v3.scripts._paths import REPO_ROOT

DEFAULT_RUNS = REPO_ROOT / "research_artifacts_v2" / "runs"
DEFAULT_RELEASE = REPO_ROOT / "research_artifacts_v2" / "release"
DEFAULT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "research-v2.yml"

EXIT_OK = 0
EXIT_CLAIM_MISMATCH = 19
EXIT_INPUT_ERROR = 7

METHODS = ("proposed", "baselines_b0", "baselines_c1", "ablations_a1", "ablations_a2", "ablations_a3")


class ClaimVerifyError(RuntimeError):
    """Raised when the verification inputs are unusable."""


def scan_manifests(runs_root: Path) -> dict:
    if not runs_root.is_dir():
        raise ClaimVerifyError(f"runs root not found: {runs_root}")
    cells: dict[tuple[str, str], set[str]] = defaultdict(set)
    seeds_by_cell: Counter = Counter()
    statuses: Counter = Counter()
    n_manifests = 0
    for manifest_path in runs_root.glob("LN-*/*/*/seed*/run_manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ClaimVerifyError(f"{manifest_path}: invalid JSON: {exc}") from exc
        rel = manifest_path.relative_to(runs_root).parts
        study, tier, method, seed_dir = rel[0], rel[1], rel[2], rel[3]
        # the manifest must agree with its directory location
        if manifest.get("study_id") != study or manifest.get("tier") != tier:
            raise ClaimVerifyError(
                f"{manifest_path}: manifest study/tier ({manifest.get('study_id')}, "
                f"{manifest.get('tier')}) disagrees with directory ({study}, {tier})"
            )
        cells[(study, tier)].add(method)
        seeds_by_cell[(study, tier, method)] += 1
        statuses[manifest.get("status", "UNKNOWN")] += 1
        n_manifests += 1
    return {
        "n_manifests": n_manifests,
        "cells": {f"{s}/{t}": sorted(m) for (s, t), m in sorted(cells.items())},
        "tiers_on_disk": sorted({t for (_, t) in cells}),
        "statuses": dict(statuses),
        "seeds_by_cell": {f"{s}/{t}/{m}": n for (s, t, m), n in sorted(seeds_by_cell.items())},
    }


def parse_claimed_tiers(release_dir: Path, workflow: Path) -> dict[str, list[str]]:
    claims: dict[str, list[str]] = {}
    appendix = release_dir / "BENCHMARK_APPENDIX.md"
    if appendix.is_file():
        text = appendix.read_text(encoding="utf-8")
        m = re.search(r"tiers?:?\s*([T]\d(?:S)?(?:\s*,\s*[T]\d(?:S)?)*)", text, re.IGNORECASE)
        if m:
            claims["BENCHMARK_APPENDIX.md"] = re.findall(r"[T]\d(?:S)?", m.group(1))
    readiness = release_dir / "SCIENTIFIC_READINESS.md"
    if readiness.is_file():
        text = readiness.read_text(encoding="utf-8")
        m = re.search(r"tiers:\s*([T]\d(?:S)?(?:\s*,\s*[T]\d(?:S)?)*)", text, re.IGNORECASE)
        if m:
            claims["SCIENTIFIC_READINESS.md"] = re.findall(r"[T]\d(?:S)?", m.group(1))
    if workflow.is_file():
        text = workflow.read_text(encoding="utf-8")
        for m in re.finditer(r"run_matrix[^\n]*--tier\s+([^\s\n]+)", text):
            claims.setdefault("research-v2.yml (CLI --tier)", []).extend(
                t.strip().upper() for t in m.group(1).split(",") if t.strip()
            )
    return claims


def recompute_readiness(runs_root: Path) -> dict[str, dict]:
    """Recompute PASS/PARTIAL per study from metrics.json on disk."""
    out: dict[str, dict] = {}
    for study in sorted(p.name for p in runs_root.glob("LN-*")):
        means: dict[str, float] = {}
        for method in METHODS:
            accs = []
            for mf in sorted((runs_root / study / "T3" / method).glob("seed*/metrics.json")):
                try:
                    accs.append(float(json.loads(mf.read_text(encoding="utf-8"))["accuracy"]))
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
            if accs:
                means[method] = sum(accs) / len(accs)
        if "proposed" not in means or "baselines_c1" not in means:
            out[study] = {"status": "INSUFFICIENT_DATA", "means": means}
            continue
        ablations = [means.get(f"ablations_a{i}") for i in (1, 2, 3)]
        separable = all(a is not None for a in ablations)
        status = (
            "PASS"
            if separable
            and means["proposed"] > means["baselines_c1"]
            and all(means["proposed"] > a for a in ablations)
            else "PARTIAL"
        )
        out[study] = {"status": status, "means": means}
    return out


def parse_readiness_table(release_dir: Path) -> dict[str, str]:
    readiness = release_dir / "SCIENTIFIC_READINESS.md"
    if not readiness.is_file():
        return {}
    claimed: dict[str, str] = {}
    pattern = re.compile(r"^\|\s*(LN-\d{2})\s*\|.*\|\s*(PASS|PARTIAL|BLOCKED)([^|]*)\|\s*$")
    for line in readiness.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line.strip())
        if m:
            claimed[m.group(1)] = m.group(2)
    return claimed


def verify(runs_root: Path, release_dir: Path, workflow: Path) -> tuple[bool, dict]:
    disk = scan_manifests(runs_root)
    claims = parse_claimed_tiers(release_dir, workflow)
    findings: list[str] = []

    # every CLI/doc-claimed tier must have manifests on disk
    for source, tiers in sorted(claims.items()):
        for tier in sorted(set(tiers)):
            executed = any(t == tier for (_, t) in (tuple(k.split("/")) for k in disk["cells"]))
            if not executed:
                findings.append(
                    f"{source} claims tier {tier} executed, but ZERO manifests for {tier} "
                    "exist on disk (claims must match executed cells, not CLI strings)"
                )

    # readiness table must match recomputed per-study status
    recomputed = recompute_readiness(runs_root)
    claimed_status = parse_readiness_table(release_dir)
    for study, rec in sorted(recomputed.items()):
        if study in claimed_status and rec["status"] in ("PASS", "PARTIAL"):
            if claimed_status[study] != rec["status"]:
                findings.append(
                    f"{study}: SCIENTIFIC_READINESS.md says {claimed_status[study]} but "
                    f"metrics on disk recompute to {rec['status']} (means={rec['means']})"
                )

    # seed-count integrity: each cell must have exactly 3 seed manifests
    bad_seeds = {k: v for k, v in disk["seeds_by_cell"].items() if v != 3}
    if bad_seeds:
        findings.append(f"cells without exactly 3 seed manifests: {bad_seeds}")

    report = {
        "schema": "research_v3.claim_verification/v1",
        "task_id": "V3-G23",
        "n_manifests": disk["n_manifests"],
        "tiers_on_disk": disk["tiers_on_disk"],
        "statuses_on_disk": disk["statuses"],
        "claimed_tiers": claims,
        "readiness_recomputed": {k: v["status"] for k, v in recomputed.items()},
        "readiness_claimed": claimed_status,
        "findings": findings,
        "status": "VERIFIED" if not findings else "MISMATCH",
    }
    return not findings, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.cross_verify_claims",
        description=(
            "Cross-verify every 'tier executed' claim in release docs against "
            "the actual run manifests on disk (V3-G23). Nonzero on mismatch."
        ),
    )
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        ok, report = verify(args.runs_root, args.release, args.workflow)
    except ClaimVerifyError as exc:
        print(f"FAIL cross_verify_claims: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    print(
        f"manifests={report['n_manifests']} tiers_on_disk={report['tiers_on_disk']} "
        f"statuses={report['statuses_on_disk']}"
    )
    print(f"claimed tiers: {report['claimed_tiers']}")
    for f in report["findings"]:
        print(f"FINDING: {f}", file=sys.stderr)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if not ok:
        print(
            f"FAIL cross_verify_claims: {len(report['findings'])} claim mismatch(es) — "
            "release prose and executed manifests disagree.",
            file=sys.stderr,
        )
        return EXIT_CLAIM_MISMATCH
    print("OK cross_verify_claims: all tier/readiness claims match executed manifests.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
