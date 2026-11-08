#!/usr/bin/env python3
"""Fail-closed 50-run verifier, checks data integrity not external scientific validity."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

from recompute_metrics import compute

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX = json.loads((ROOT / "configs" / "experiments.json").read_text(encoding="utf-8"))


def sha(p: pathlib.Path | str) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def resolve_manifest_and_fixtures(original_spec: Optional[pathlib.Path]) -> tuple[Optional[dict], Optional[pathlib.Path]]:
    mf_candidates = []
    if original_spec is not None:
        mf_candidates.extend([
            original_spec / "04_FIXTURES" / "CONCRETE" / "fixture_manifest.json",
            original_spec / "fixtures" / "fixture_manifest.json",
            original_spec / "fixture_manifest.json",
        ])
    mf_candidates.extend([
        ROOT / "fixtures" / "fixture_manifest.json",
        ROOT.parent / "research" / "fixtures" / "fixture_manifest.json",
        ROOT.parent / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026" / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026" / "04_FIXTURES" / "CONCRETE" / "fixture_manifest.json",
    ])

    for mf in mf_candidates:
        if mf.is_file():
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                return data, mf.parent
            except Exception:
                continue
    return None, None


def resolve_fixture_file(paper: str, original_spec: Optional[pathlib.Path], fixtures_dir: Optional[pathlib.Path]) -> Optional[pathlib.Path]:
    candidates = []
    if fixtures_dir:
        candidates.append(fixtures_dir / f"{paper}_concrete.jsonl")
    if original_spec:
        candidates.extend([
            original_spec / "04_FIXTURES" / "CONCRETE" / f"{paper}_concrete.jsonl",
            original_spec / "fixtures" / f"{paper}_concrete.jsonl",
            original_spec / f"{paper}_concrete.jsonl",
        ])
    candidates.extend([
        ROOT / "fixtures" / f"{paper}_concrete.jsonl",
        ROOT.parent / "research" / "fixtures" / f"{paper}_concrete.jsonl",
        ROOT.parent / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026" / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026" / "04_FIXTURES" / "CONCRETE" / f"{paper}_concrete.jsonl",
    ])
    for c in candidates:
        if c.is_file():
            return c
    return None


def check(output: pathlib.Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    output = pathlib.Path(output).resolve()
    problems: List[str] = []
    register: List[Dict[str, Any]] = []
    all_runs: set[str] = set()
    studyinfo: Dict[str, Any] = {}
    locked_sha: Optional[str] = None
    original_spec: Optional[pathlib.Path] = None

    context_path = output / "run_context.json"
    if context_path.is_file():
        try:
            context = json.loads(context_path.read_text(encoding="utf-8"))
            if context.get("original_spec"):
                original_spec = pathlib.Path(context["original_spec"])
        except Exception as e:
            problems.append(f"Cannot parse run_context.json: {e}")

    fixtures_manifest, fixtures_dir = resolve_manifest_and_fixtures(original_spec)
    if fixtures_manifest is None:
        problems.append("Original immutable fixture manifest unavailable across standard repo paths")

    for paper, dat in MATRIX["studies"].items():
        observed: List[str] = []
        ref_case_hashes: Optional[Dict[str, str]] = None
        ref_source_fixture: Optional[str] = None
        expected_case_hashes: Optional[Dict[str, str]] = None
        expected_fixture_sha: Optional[str] = None

        source_file = resolve_fixture_file(paper, original_spec, fixtures_dir)
        if source_file is not None and fixtures_manifest is not None:
            try:
                cohort_info = fixtures_manifest.get("cohorts", {}).get(paper, {})
                expected_fixture_sha = cohort_info.get("sha256")
                actual_fixture_sha = sha(source_file)
                if expected_fixture_sha and actual_fixture_sha != expected_fixture_sha:
                    raise ValueError(f"Source file differs from fixture manifest: {actual_fixture_sha} != {expected_fixture_sha}")
                fixture_rows = [json.loads(t) for t in source_file.read_text(encoding="utf-8").splitlines() if t.strip()]
                expected_case_hashes = {r["case_id"]: r["input_hash"] for r in fixture_rows}
                if len(expected_case_hashes) != 720:
                    raise ValueError(f"Expected 720 cases in manifest, saw {len(expected_case_hashes)}")
            except Exception as e:
                problems.append(f"{paper}: cannot validate original fixture: {e}")
        elif source_file is None:
            problems.append(f"{paper}: missing authoritative concrete fixture file")

        for entry in dat["runs"]:
            rid = entry["id"]
            d = output / paper / rid
            required = ["trace.jsonl", "manifest.json", "study_metric.json", "config.json", "execution_log.txt"]
            missing = [x for x in required if not (d / x).is_file()]
            if missing:
                problems.append(f"{paper}/{rid}: MISSING {missing}")
                continue
            try:
                ma = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
                met = json.loads((d / "study_metric.json").read_text(encoding="utf-8"))
                cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
                rows = [json.loads(x) for x in (d / "trace.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

                if not ma.get("run_id") or ma["run_id"] in all_runs:
                    raise ValueError("missing or duplicate run id")
                all_runs.add(ma["run_id"])
                if ma.get("status") != "EXECUTED" or ma.get("paper_id") != paper or ma.get("mode") != entry["mode"]:
                    raise ValueError("manifest paper/mode/status mismatch")
                if ma.get("adapter") != dat["adapter"]:
                    raise ValueError("adapter mismatch")
                if cfg != entry["config"] or ma.get("config") != cfg:
                    raise ValueError("config differs from frozen matrix")
                if ma.get("baseline_repository_commit") != MATRIX["old_spec_ancestral_commit"]:
                    raise ValueError("incorrect ancestral baseline")
                if sha(d / "trace.jsonl") != ma.get("trace_sha256"):
                    raise ValueError("trace SHA mismatch")
                if ma.get("cases_run") != len(rows) or ma.get("adapter_errors") != 0:
                    raise ValueError("wrong count or adapter errors")

                sha_repo = ma.get("source_commit_at_runtime")
                base_repo = ma.get("repository_provenance", {}).get("head_sha")
                if sha_repo != base_repo:
                    raise ValueError("source SHA mismatch inside manifest")
                if locked_sha is None:
                    locked_sha = sha_repo
                elif sha_repo != locked_sha:
                    raise ValueError("different source SHA across runs")

                case_map: Dict[str, str] = {}
                for row in rows:
                    if row.get("run_id") != ma["run_id"] or row.get("paper_id") != paper or row.get("mode") != entry["mode"] or row.get("error") is not None:
                        raise ValueError("trace row bad metadata or adapter exception")
                    cid = row.get("case_id")
                    if not cid or cid in case_map:
                        raise ValueError("duplicate or missing case ID")
                    case_map[cid] = row.get("input_hash", "")

                if expected_case_hashes is not None and len(rows) == 720 and case_map != expected_case_hashes:
                    raise ValueError("Trace case_id/input hashes differ from authoritative spec")
                if expected_fixture_sha is not None and ma.get("source_fixture_sha256") != expected_fixture_sha:
                    raise ValueError("Manifest fixture SHA differs from authoritative source")
                if ref_case_hashes is None:
                    ref_case_hashes = case_map
                elif case_map != ref_case_hashes:
                    raise ValueError("not paired, case hashes differ")
                if ref_source_fixture is None:
                    ref_source_fixture = ma.get("source_fixture_sha256")
                elif ma.get("source_fixture_sha256") != ref_source_fixture:
                    raise ValueError("fixture SHA differs across conditions")

                real_calc = compute(d)
                for k in ("paper_id", "run_id", "mode", "metric_key", "numerator", "denominator", "value", "unit", "direction", "trace_sha256", "manifest_file_sha256"):
                    if met.get(k) != real_calc.get(k):
                        raise ValueError(f"study metric mismatch in {k}: {met.get(k)} != {real_calc.get(k)}")

                observed.append(rid)
                register.append({
                    "paper_id": paper,
                    "condition": rid,
                    "mode": entry["mode"],
                    "label": entry["label"],
                    "source_sha": sha_repo,
                    "run_id": ma["run_id"],
                    "trace_sha256": ma["trace_sha256"],
                    "manifest_sha256": sha(d / "manifest.json"),
                    "metric_sha256": sha(d / "study_metric.json"),
                    "fixture_sha256": ma.get("source_fixture_sha256"),
                    "metric_key": met["metric_key"],
                    "numerator": met["numerator"],
                    "denominator": met["denominator"],
                    "value": met["value"],
                    "unit": met["unit"],
                    "synthetic_policy_only": True,
                    "journal_ready": False,
                })
            except Exception as e:
                problems.append(f"{paper}/{rid}: {type(e).__name__}: {e}")

        studyinfo[paper] = {
            "runs_verified": len(observed),
            "verified_conditions": observed,
            "status": "TECHNICAL_COMPLETE" if len(observed) == 5 else "BLOCKED",
        }

    good = len(register) == 50 and not problems
    report = {
        "status": "SOFTWARE_EVIDENCE_TECHNICALLY_COMPLETE" if good else "BLOCKED",
        "is_scientific_submission_approved": False,
        "reason": "External validation / provenance / novelty / CI reviewed separately",
        "locked_repo_sha": locked_sha,
        "verified_runs": len(register),
        "case_executions": sum(x["denominator"] for x in register) if False else len(register) * 720,
        "per_study": studyinfo,
        "blockers": problems,
    }
    return report, register


def main():
    a = argparse.ArgumentParser(description="Verify technical integrity of research release runs")
    a.add_argument("--output", type=pathlib.Path, required=True)
    o = a.parse_args().output.resolve()
    report, registry = check(o)
    o.mkdir(parents=True, exist_ok=True)
    (o / "release_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = [
        "paper_id", "condition", "mode", "label", "source_sha", "run_id",
        "trace_sha256", "manifest_sha256", "metric_sha256", "fixture_sha256",
        "metric_key", "numerator", "denominator", "value", "unit",
        "synthetic_policy_only", "journal_ready",
    ]
    with (o / "evidence_registry.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(registry)

    summary = {
        "status": report["status"],
        "verified_runs": report["verified_runs"],
        "case_executions": report["case_executions"],
        "blockers": report["blockers"][:30],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "SOFTWARE_EVIDENCE_TECHNICALLY_COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
