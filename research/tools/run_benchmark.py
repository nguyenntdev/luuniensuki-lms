#!/usr/bin/env python3
"""Execute ACTUAL connected research policy adapter on a frozen synthetic corpus.

Usage:
  python research/tools/run_benchmark.py --paper LN-06 --mode baseline \\
    --adapter research.integrations.ln06:run_policy --run-dir artifacts/LN-06/baseline

Adapter callable contract:
  def run_policy(scenario_input: dict, *, mode: str, config: dict) -> dict:
      return {'decision': 'find_valid_route', 'reason_codes': [...],
              'policy_version': '...', ...study-specific measurable fields...}

No adapter = NO EXECUTION. No synthetic outcome or expected decision is passed
into the adapter. The runner does not change GitHub source or production DB.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
import pathlib
import platform
import subprocess
import sys
import time
import traceback
import uuid


def sha(p: pathlib.Path | str) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def load_callable(spec: str):
    mod, sep, fn = spec.partition(":")
    if not sep:
        raise ValueError("Adapter must be module:function")
    module = importlib.import_module(mod)
    func = getattr(module, fn)
    if not callable(func):
        raise TypeError("Adapter is not callable")
    return func


def git_output(repo_root: pathlib.Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()[:500]}")
    return result.stdout.strip()


def repo_provenance(repo_root: pathlib.Path, allow_dirty: bool = False) -> dict:
    root = repo_root.resolve()
    if not (root / ".git").exists():
        raise ValueError(f"Not a Git checkout: {root}")
    head = git_output(root, ["rev-parse", "HEAD"])
    dirty = git_output(root, ["status", "--porcelain"])
    if dirty and not allow_dirty:
        raise ValueError("Working tree dirty; commit changes or pass --allow-uncommitted for development only")
    base = "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
    result = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, head])
    if result.returncode != 0:
        raise ValueError("Research checkout is not a descendant of pinned baseline commit")
    return {
        "repo_path": str(root),
        "head_sha": head,
        "dirty": bool(dirty),
        "base_sha": base,
        "branch": git_output(root, ["rev-parse", "--abbrev-ref", "HEAD"]),
    }


def resolve_fixture_file(
    paper: str,
    fixture_file: pathlib.Path | None = None,
    fixtures_dir: pathlib.Path | None = None,
    repo_root: pathlib.Path | None = None,
) -> pathlib.Path:
    if fixture_file and fixture_file.is_file():
        return fixture_file.resolve()
    if fixtures_dir and (fixtures_dir / f"{paper}_concrete.jsonl").is_file():
        return (fixtures_dir / f"{paper}_concrete.jsonl").resolve()

    here = pathlib.Path(__file__).resolve()
    research_dir = here.parents[1]
    candidates = [
        research_dir / "fixtures" / f"{paper}_concrete.jsonl",
        research_dir / "04_FIXTURES" / "CONCRETE" / f"{paper}_concrete.jsonl",
    ]
    if repo_root:
        candidates.extend([
            repo_root / "research" / "fixtures" / f"{paper}_concrete.jsonl",
            repo_root / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026" / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026" / "04_FIXTURES" / "CONCRETE" / f"{paper}_concrete.jsonl",
        ])
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()

    raise FileNotFoundError(f"Cannot find fixture for {paper} across standard locations: {candidates}")


def main():
    p = argparse.ArgumentParser(description="Execute research policy adapter on synthetic corpus")
    p.add_argument("--paper", required=True, choices=[f"LN-{i:02d}" for i in range(1, 11)])
    p.add_argument("--mode", required=True, choices=["baseline", "intervention", "ablation"])
    p.add_argument("--adapter", required=True, help="module:function in checked-out research implementation")
    p.add_argument("--run-dir", required=True, type=pathlib.Path)
    p.add_argument("--config", type=pathlib.Path)
    p.add_argument("--max-cases", type=int, default=None)
    p.add_argument("--fail-fast", action="store_true")
    p.add_argument("--repo-root", type=pathlib.Path, default=None, help="Local Git checkout based on pinned commit")
    p.add_argument("--allow-uncommitted", action="store_true", help="Development only: results not suitable for publication")
    p.add_argument("--fixture-file", type=pathlib.Path, default=None)
    p.add_argument("--fixtures-dir", type=pathlib.Path, default=None)
    a = p.parse_args()

    repo_root = a.repo_root or pathlib.Path(__file__).resolve().parents[2]
    repo_root = repo_root.resolve()

    src = resolve_fixture_file(a.paper, a.fixture_file, a.fixtures_dir, repo_root)

    config = json.loads(a.config.read_text(encoding="utf-8")) if a.config and a.config.is_file() else {}
    if not isinstance(config, dict):
        raise TypeError("Config must be JSON object")

    provenance = repo_provenance(repo_root, a.allow_uncommitted)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    fn = load_callable(a.adapter)
    a.run_dir.mkdir(parents=True, exist_ok=True)
    trace = a.run_dir / "trace.jsonl"
    if trace.exists():
        raise FileExistsError(f"Refusing overwrite: {trace}")

    runid = str(uuid.uuid4())
    start = dt.datetime.now(dt.timezone.utc)
    passed = 0
    failed = 0
    errored = 0
    lines = 0
    elapsed = []

    with trace.open("w", encoding="utf-8") as f:
        for row in src.open(encoding="utf-8"):
            if not row.strip():
                continue
            if a.max_cases is not None and lines >= a.max_cases:
                break
            case = json.loads(row)
            t = time.perf_counter()
            error = None
            result = {}
            try:
                result = fn(case["input"], mode=a.mode, config=config)
                if not isinstance(result, dict) or not isinstance(result.get("decision"), str):
                    raise ValueError("Adapter must return {decision: str, ...}")
            except Exception as exc:
                error = {
                    "type": type(exc).__name__,
                    "message": str(exc)[:1000],
                    "traceback": traceback.format_exc(limit=3),
                }
                result = {"decision": "__ADAPTER_EXCEPTION__", "reason_codes": ["adapter_exception"]}
                errored += 1
            sec = round((time.perf_counter() - t) * 1000, 4)
            elapsed.append(sec)
            expected_decision = case.get("oracle", {}).get("expected_decision")
            ok = (result["decision"] == expected_decision) and error is None
            passed += int(ok)
            failed += int(not ok)
            record = {
                "run_id": runid,
                "paper_id": a.paper,
                "case_id": case["case_id"],
                "mode": a.mode,
                "fault_id": case["fault_id"],
                "input_hash": case["input_hash"],
                "policy_version": str(result.get("policy_version", "unversioned")),
                "decision": result["decision"],
                "reason_codes": result.get("reason_codes", []),
                "expected_decision": expected_decision,
                "oracle_match": ok,
                "observables": {k: v for k, v in result.items() if k not in ("decision", "reason_codes")},
                "elapsed_ms": sec,
                "error": error,
            }
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
            lines += 1
            if a.fail_fast and not ok:
                break

    manifest = {
        "run_id": runid,
        "status": "EXECUTED",
        "paper_id": a.paper,
        "mode": a.mode,
        "adapter": a.adapter,
        "source_fixture_sha256": sha(src),
        "config": config,
        "source_commit_at_runtime": provenance["head_sha"],
        "repository_provenance": provenance,
        "publishable_run": not provenance["dirty"],
        "baseline_repository_commit": "54da2beb71f3df70e1f00b215ae0fb1a850eb263",
        "time_started_utc": start.isoformat(),
        "time_finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "python": platform.python_version(),
        "trace_sha256": sha(trace),
        "cases_run": lines,
        "oracle_matches": passed,
        "oracle_mismatches": failed,
        "adapter_errors": errored,
        "sampling_unit": "synthetic_scenario",
        "learning_outcome_study": False,
    }
    (a.run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_dir": str(a.run_dir), "cases_run": lines, "matches": passed, "mismatches": failed, "errors": errored}, ensure_ascii=False))
    if errored:
        sys.exit(2)


if __name__ == "__main__":
    main()
