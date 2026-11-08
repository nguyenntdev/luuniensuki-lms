#!/usr/bin/env python3
"""Execute 10×5 fixed-source policy benchmark runs; no code/data synthesis or paper editing.

Must run only after fixable repo CI/test failures are corrected and code is frozen.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import subprocess
import sys
from typing import Any, Dict, List, Optional

from check_sources import verify_spec

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX = json.loads((ROOT / "configs" / "experiments.json").read_text(encoding="utf-8"))


def git(repo: pathlib.Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def resolve_benchmark_runner(spec: Optional[pathlib.Path] = None) -> pathlib.Path:
    candidates = []
    if spec:
        candidates.extend([
            spec / "tools" / "run_benchmark.py",
            spec / "run_benchmark.py",
        ])
    candidates.extend([
        ROOT / "tools" / "run_benchmark.py",
        ROOT.parent / "research" / "tools" / "run_benchmark.py",
        ROOT.parent / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026" / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026" / "tools" / "run_benchmark.py",
    ])
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    raise FileNotFoundError(f"Cannot find run_benchmark.py across standard locations: {candidates}")


def run_one(
    study: str,
    datum: dict,
    repo: pathlib.Path,
    runner_script: pathlib.Path,
    output: pathlib.Path,
    sha: str,
    allow_uncommitted: bool = False,
    max_cases: Optional[int] = None,
) -> Dict[str, Any]:
    sdir = output / study
    sdir.mkdir(parents=True, exist_ok=True)
    for run in datum["runs"]:
        run_id = run["id"]
        dst = sdir / run_id
        if dst.exists():
            raise FileExistsError(f"{dst} already exists; NEVER overwrite a run")
        dst.mkdir(parents=True)
        cfgpath = dst / "config.json"
        cfgpath.write_text(json.dumps(run["config"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        cmd = [
            sys.executable,
            str(runner_script),
            "--repo-root",
            str(repo),
            "--paper",
            study,
            "--mode",
            run["mode"],
            "--adapter",
            datum["adapter"],
            "--config",
            str(cfgpath),
            "--run-dir",
            str(dst),
        ]
        if allow_uncommitted:
            cmd.append("--allow-uncommitted")
        if max_cases is not None:
            cmd.extend(["--max-cases", str(max_cases)])

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        log_content = (
            "COMMAND: "
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
            + "\nEXIT_CODE: "
            + str(result.returncode)
            + "\n"
        )
        (dst / "execution_log.txt").write_text(log_content, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"{study}/{run_id}: failed code={result.returncode}, log={dst/'execution_log.txt'}")

        met_script = ROOT / "tools" / "recompute_metrics.py"
        met = subprocess.run([sys.executable, str(met_script), str(dst)], capture_output=True, text=True, env=env)
        with (dst / "execution_log.txt").open("a", encoding="utf-8") as f:
            f.write(
                "\nMETRIC_STDOUT:\n"
                + met.stdout
                + "\nMETRIC_STDERR:\n"
                + met.stderr
                + "\nMETRIC_EXIT_CODE: "
                + str(met.returncode)
                + "\n"
            )
        if met.returncode != 0:
            raise RuntimeError(f"{study}/{run_id}: metric failed: {met.stderr[:300]}")

        current_sha = git(repo, "rev-parse", "HEAD")
        if current_sha != sha:
            raise RuntimeError(f"{study}/{run_id}: repository HEAD changed mid benchmark: {current_sha} != {sha}")
        if not allow_uncommitted and git(repo, "status", "--porcelain"):
            raise RuntimeError(f"{study}/{run_id}: repository became dirty mid benchmark")

    return {"study": study, "status": "PASS", "conditions": len(datum["runs"])}


def run_benchmark_suite(
    repo: pathlib.Path,
    output: pathlib.Path,
    spec: Optional[pathlib.Path] = None,
    workers: int = 10,
    studies_filter: str = "all",
    allow_uncommitted: bool = False,
    max_cases: Optional[int] = None,
) -> Dict[str, Any]:
    repo = repo.resolve()
    output = output.resolve()
    spec = spec.resolve() if spec else None

    if output == repo:
        raise ValueError("Output must not be repository root to avoid dirtying git state")

    dirty = git(repo, "status", "--porcelain")
    if dirty and not allow_uncommitted:
        raise RuntimeError("Working tree dirty. Commit changes before publication benchmark or pass --allow-uncommitted.")

    sha = git(repo, "rev-parse", "HEAD")
    base_commit = MATRIX["old_spec_ancestral_commit"]
    try:
        subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", base_commit, sha], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Current commit {sha} is not a descendant of ancestral commit {base_commit}")

    runner_script = resolve_benchmark_runner(spec)

    source_audit = verify_spec(spec)
    if source_audit["issues"]:
        raise RuntimeError(f"Fixture validation failed: {source_audit['issues'][:5]}")

    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory {output} must be new or empty; refusing overwrite")
    output.mkdir(parents=True, exist_ok=True)

    studies = sorted(MATRIX["studies"]) if studies_filter == "all" else [x.strip() for x in studies_filter.split(",")]
    for s in studies:
        if s not in MATRIX["studies"]:
            raise ValueError(f"Unknown study ID: {s}")

    if not 1 <= workers <= 10:
        raise ValueError("workers must be 1..10")

    run_ctx = {
        "locked_commit": sha,
        "original_spec": str(spec or (ROOT / "fixtures")),
        "study_ids": studies,
        "mode_count": 5,
        "synthetic_not_human": True,
        "allow_uncommitted": allow_uncommitted,
        "max_cases": max_cases,
    }
    (output / "run_context.json").write_text(json.dumps(run_ctx, indent=2) + "\n", encoding="utf-8")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {
            pool.submit(
                run_one,
                s,
                MATRIX["studies"][s],
                repo,
                runner_script,
                output,
                sha,
                allow_uncommitted,
                max_cases,
            ): s
            for s in studies
        }
        for future in concurrent.futures.as_completed(jobs):
            s = jobs[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append({"study": s, "status": "FAIL", "error": str(e)})

    good = all(x.get("status") == "PASS" for x in results)
    report = {
        "status": "PASS" if good else "FAIL",
        "locked_commit": sha,
        "results": sorted(results, key=lambda x: x["study"]),
    }
    (output / "orchestration_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main():
    ap = argparse.ArgumentParser(description="Execute full 50-condition research policy benchmark matrix")
    ap.add_argument("--repo", type=pathlib.Path, default=None, help="Path to repo root (defaults to repo containing this script)")
    ap.add_argument("--spec", type=pathlib.Path, default=None, help="Path to spec directory (optional; defaults to repo research/fixtures)")
    ap.add_argument("--output", type=pathlib.Path, required=True, help="Destination directory for run outputs")
    ap.add_argument("--workers", type=int, default=10, help="Number of concurrent worker threads (1..10)")
    ap.add_argument("--studies", default="all", help="Comma-separated list of study IDs (e.g. LN-01,LN-02) or 'all'")
    ap.add_argument("--allow-uncommitted", action="store_true", help="Development mode: allow uncommitted working tree changes")
    ap.add_argument("--max-cases", type=int, default=None, help="Limit cases per run (useful for fast verification)")
    a = ap.parse_args()

    repo = (a.repo or ROOT.parent).resolve()
    report = run_benchmark_suite(
        repo=repo,
        output=a.output,
        spec=a.spec,
        workers=a.workers,
        studies_filter=a.studies,
        allow_uncommitted=a.allow_uncommitted,
        max_cases=a.max_cases,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
