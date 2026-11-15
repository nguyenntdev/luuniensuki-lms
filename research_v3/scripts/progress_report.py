"""Conservative progress report for the Research V3 task register.

Recomputes DONE/BLOCKED for every task in
``LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115/06_TASK_TRACKER/V3_TASK_REGISTER.csv``
from on-disk artifacts only. The register's own ``status`` column is ignored
(all rows are TODO); nothing is promoted on assertion.

Rule (conservative, fail-closed):
- ``human_only=true`` -> BLOCKED, always. A human-only task found marked DONE
  in any machine-readable task ledger is a hard error (exit code 2).
- Non-human task WITH an entry in its paper's machine-readable task ledger:
  DONE only when ALL of the following hold:
    1. the ledger status is a completed status (DONE, DONE_ENGINEERING,
       ENGINEERING_PASS, EVIDENCE_VERIFIED, CODE_READY);
    2. the paper run dir ``research_artifacts_v3/runs/pXX`` holds >= 1 file;
    3. every path-like evidence path the ledger lists exists on disk, and at
       least one exists when path-like evidence is listed.
  Anything else -> BLOCKED, with the exact ledger status recorded as reason.
- Non-human task WITHOUT a task-granular ledger -> BLOCKED ("paper-level
  artifacts only; per-task DONE requires a machine-readable task ledger").
- GLOBAL tasks are DONE only when their named artifact exists (static map);
  V3-G19 stays BLOCKED (external double-blind rerun not executed; only the
  request artifact is staged).

The script also verifies every paper P01..P14 has a non-empty
``research_artifacts_v3/runs/pXX`` directory. Missing/empty -> exit code 1.

Exit codes: 0 = consistent; 1 = missing paper artifacts; 2 = human-only task
marked DONE somewhere.

Usage:
  python -m research_v3.scripts.progress_report
  python -m research_v3.scripts.progress_report --output /tmp/progress.json
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from research_v3.scripts._paths import REPO_ROOT, RELEASE_DIR, RUNS_DIR

TASK_REGISTER = (
    REPO_ROOT
    / "LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115"
    / "06_TASK_TRACKER"
    / "V3_TASK_REGISTER.csv"
)

PAPERS = [f"P{i:02d}" for i in range(1, 15)]

# Machine-readable, per-task status ledgers that this script accepts as
# evidence. Papers not listed here have no task-granular ledger, so their
# non-human tasks cannot be marked DONE by this script.
TASK_LEDGERS: dict[str, tuple[Path, str]] = {
    "P01": (REPO_ROOT / "research_artifacts_v3/runs/p01/status.json", "flat"),
    "P02": (REPO_ROOT / "research_artifacts_v3/runs/p02/task_status.json", "detailed"),
    "P03": (REPO_ROOT / "research_artifacts_v3/runs/p03/task_status.json", "detailed"),
    "P04": (REPO_ROOT / "research_artifacts_v3/runs/p04/status/p04_status.json", "detailed"),
    "P05": (REPO_ROOT / "research_artifacts_v3/runs/p05/task_status.json", "detailed"),
    "P06": (REPO_ROOT / "research_artifacts_v3/runs/p06/task_status.json", "detailed"),
    "P07": (REPO_ROOT / "research_artifacts_v3/runs/p07/task_status.json", "detailed"),
    "P08": (REPO_ROOT / "research_artifacts_v3/runs/p08/task_status.json", "detailed"),
    "P09": (REPO_ROOT / "research_artifacts_v3/runs/p09/task_status.json", "detailed"),
    "P10": (REPO_ROOT / "research_artifacts_v3/runs/p10/task_status.json", "detailed"),
    "P13": (REPO_ROOT / "research_artifacts_v3/runs/p13/task_status.json", "detailed"),
    "P14": (REPO_ROOT / "research_artifacts_v3/runs/p14/task_status.json", "detailed"),
    "P11": (REPO_ROOT / "research_artifacts_v3/runs/p11/status_manifest.json", "list"),
    "P12": (REPO_ROOT / "research_artifacts_v3/runs/p12/progress.json", "flat"),
}

DONE_STATUSES = {"DONE", "DONE_ENGINEERING", "ENGINEERING_PASS", "EVIDENCE_VERIFIED", "CODE_READY"}

# GLOBAL tasks: the single artifact that must exist on disk for DONE.
# GLOBAL tasks absent from this map stay BLOCKED.
GLOBAL_TASK_ARTIFACTS: dict[str, tuple[Path, str]] = {
    "V3-G00": (REPO_ROOT / "research_v3/data_frozen/source_lock.json", "source hash lock"),
    "V3-G01": (REPO_ROOT / "research_v3/governance/claims/claims_ledger.csv", "claims ledger"),
    "V3-G02": (REPO_ROOT / "research_v3/datasets/registry.yaml", "dataset registry"),
    "V3-G03": (REPO_ROOT / "research_v3/contracts/cards.py", "contract cards"),
    "V3-G04": (REPO_ROOT / "research_v3/eval/splitters.py", "group/time splitters"),
    "V3-G05": (REPO_ROOT / "research_v3/baselines/verification/verify_baselines.py", "baseline verification"),
    "V3-G06": (REPO_ROOT / "research_v3/scripts/replicate.py", "replication guard"),
    "V3-G07": (REPO_ROOT / "research_v3/eval/statistics.py", "statistics module"),
    "V3-G08": (REPO_ROOT / "research_v3/annotations/tasks", "annotation tasks dir"),
    "V3-G10": (REPO_ROOT / "research_v3/scripts/render.py", "render pipeline"),
    "V3-G11": (REPO_ROOT / "research_v3/data_frozen/source_lock_20261115T133004Z.json", "refreshed source lock"),
    "V3-G12": (REPO_ROOT / ".github/workflows/research-v3.yml", "CI workflow"),
    "V3-G13": (REPO_ROOT / "research_v3/scripts/replicate.py", "stochastic/deterministic guard"),
    "V3-G14": (REPO_ROOT / "research_v3/scripts/label_mismatch_audit.py", "label mismatch audit"),
    "V3-G15": (REPO_ROOT / "research_v3/scripts/stress_parity.py", "LN-06 solver parity"),
    "V3-G16": (REPO_ROOT / "research_v3/scripts/stress_parity.py", "LN-07 scored stress"),
    "V3-G17": (REPO_ROOT / "research_v3/scripts/stress_parity.py", "LN-09 small-cohort stress"),
    "V3-G18": (REPO_ROOT / "research_v3/scripts/cross_paper_dedup.py", "cross-paper dedup"),
    "V3-G21": (REPO_ROOT / "tests/research_v3/integration/test_matrix_selection.py", "matrix selection tests"),
    "V3-G22": (REPO_ROOT / "research_artifacts_v2/release/BENCHMARK_APPENDIX.md", "benchmark appendix"),
    "V3-G23": (REPO_ROOT / "research_v3/scripts/cross_verify_claims.py", "tier cross-verification"),
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def _run_dir(paper_id: str) -> Path:
    return RUNS_DIR / paper_id.lower()


def _run_file_count(paper_id: str) -> int:
    run_dir = _run_dir(paper_id)
    if not run_dir.is_dir():
        return 0
    return sum(1 for p in run_dir.rglob("*") if p.is_file())


def _load_register() -> list[dict[str, str]]:
    with TASK_REGISTER.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _norm_status(raw: str) -> str:
    """First token, uppercased: 'PARTIAL (x)' -> 'PARTIAL'."""
    return re.split(r"[\s(:]", raw.strip(), maxsplit=1)[0].upper()


def _path_like(value: str) -> bool:
    """A string that looks like a repo-relative file path (no whitespace)."""
    v = value.strip()
    return bool(v) and not any(c.isspace() for c in v) and "://" not in v and not v.startswith("http")


def _evidence_paths(entry: dict) -> list[str]:
    paths: list[str] = []
    for key in ("outputs", "evidence", "artifacts"):
        val = entry.get(key)
        if isinstance(val, str):
            val = [val]
        if isinstance(val, list):
            paths.extend(v for v in val if isinstance(v, str))
    return paths


def _existing_repo_paths(raw_paths: list[str]) -> tuple[list[str], list[str]]:
    """Split raw evidence strings into (existing repo paths, path-like-but-missing)."""
    existing: list[str] = []
    missing: list[str] = []
    for raw in raw_paths:
        if not _path_like(raw):
            continue  # prose evidence ("run payload corpus block") is not a path claim
        candidate = raw.split("#", 1)[0].split("::", 1)[0].strip()
        if not candidate:
            continue
        if (REPO_ROOT / candidate).exists():
            existing.append(raw)
        else:
            missing.append(raw)
    return existing, missing


def _load_ledger(paper_id: str) -> tuple[dict[str, dict], Path | None, str | None]:
    """Return {task_id: normalized entry}, ledger path, error."""
    spec = TASK_LEDGERS.get(paper_id)
    if spec is None:
        return {}, None, None
    path, fmt = spec
    if not path.is_file():
        return {}, path, "ledger file missing on disk"
    try:
        if fmt == "yaml":
            import yaml

            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            tasks_raw = data.get("tasks") or {}
            entries: dict[str, dict] = {}
            for tid, val in tasks_raw.items():
                entries[str(tid)] = val if isinstance(val, dict) else {"status": str(val)}
            return entries, path, None
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks_raw = data.get("tasks") or {}
        if fmt == "list":
            entries = {}
            for item in tasks_raw:
                if isinstance(item, dict) and item.get("id"):
                    entries[str(item["id"])] = item
            return entries, path, None
        entries = {}
        for tid, val in tasks_raw.items():
            entries[str(tid)] = val if isinstance(val, dict) else {"status": str(val)}
        return entries, path, None
    except Exception as exc:  # pragma: no cover - defensive
        return {}, path, f"ledger parse error: {exc}"


def classify_task(row: dict[str, str], ledgers: dict[str, dict[str, dict]], run_files: int) -> dict:
    task_id = row["task_id"]
    paper_id = row["paper_id"]
    human_only = row["human_only"].strip().lower() == "true"

    record: dict = {
        "task_id": task_id,
        "paper_id": paper_id,
        "name": row["name"],
        "human_only": human_only,
        "register_status": row["status"],
    }

    if human_only:
        # Hard rule: human-only tasks are ALWAYS BLOCKED, whatever any ledger says.
        ledger_entry = ledgers.get(paper_id, {}).get(task_id)
        ledger_status = _norm_status(str(ledger_entry.get("status", ""))) if ledger_entry else None
        if ledger_status in DONE_STATUSES:
            record["violation"] = f"human-only task marked {ledger_status} in {TASK_LEDGERS[paper_id][0]}"
        record["status"] = "BLOCKED"
        record["reason"] = "human-only: ethics/novelty/venue signoff cannot be produced by code"
        return record

    if paper_id == "GLOBAL":
        artifact = GLOBAL_TASK_ARTIFACTS.get(task_id)
        if task_id == "V3-G19":
            record["status"] = "BLOCKED"
            record["reason"] = (
                "external double-blind rerun not executed; only the request artifact is staged "
                "(research_artifacts_v3/runs/p08/request_2026q1-rerun.json)"
            )
            return record
        if artifact is None:
            record["status"] = "BLOCKED"
            record["reason"] = "no named artifact rule for this GLOBAL task"
            return record
        path, label = artifact
        if path.exists():
            record["status"] = "DONE"
            record["reason"] = f"artifact exists: {label}"
            record["evidence"] = [str(path.relative_to(REPO_ROOT))]
        else:
            record["status"] = "BLOCKED"
            record["reason"] = f"required artifact missing on disk: {path.relative_to(REPO_ROOT)}"
        return record

    entry = ledgers.get(paper_id, {}).get(task_id)
    if entry is None:
        record["status"] = "BLOCKED"
        ledger_path = TASK_LEDGERS.get(paper_id)
        if ledger_path is None:
            record["reason"] = (
                f"no task-granular status ledger for {paper_id} "
                f"(paper-level run artifacts: {run_files} file(s) under runs/{paper_id.lower()}/); "
                "per-task DONE requires a machine-readable task ledger"
            )
        else:
            record["reason"] = f"no ledger entry for {task_id}"
        return record

    status = _norm_status(str(entry.get("status", "")))
    record["ledger_status"] = status
    if status not in DONE_STATUSES:
        record["status"] = "BLOCKED"
        record["reason"] = f"ledger status: {status or 'UNSET'}"
        return record

    if run_files < 1:
        record["status"] = "BLOCKED"
        record["reason"] = f"ledger status {status} but runs/{paper_id.lower()}/ has no files"
        return record

    existing, missing = _existing_repo_paths(_evidence_paths(entry))
    if missing:
        record["status"] = "BLOCKED"
        record["reason"] = f"ledger status {status} but evidence path(s) missing: {', '.join(missing)}"
        return record
    record["evidence"] = existing
    record["status"] = "DONE"
    record["reason"] = f"ledger status {status} + evidence on disk + non-empty run dir"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RELEASE_DIR / "progress.json")
    args = parser.parse_args(argv)

    rows = _load_register()
    ledgers: dict[str, dict[str, dict]] = {}
    ledger_errors: dict[str, str] = {}
    for paper_id in TASK_LEDGERS:
        entries, path, err = _load_ledger(paper_id)
        ledgers[paper_id] = entries
        if err:
            ledger_errors[paper_id] = err

    run_files = {p: _run_file_count(p) for p in PAPERS}

    violations: list[str] = []
    records = [classify_task(row, ledgers, run_files.get(row["paper_id"], 0)) for row in rows]
    for rec in records:
        if rec.get("violation"):
            violations.append(rec["violation"])

    missing_papers = [p for p in PAPERS if run_files[p] < 1]

    by_status = {"DONE": 0, "BLOCKED": 0}
    for rec in records:
        by_status[rec["status"]] += 1

    non_human = [r for r in records if not r["human_only"]]
    human_only = [r for r in records if r["human_only"]]

    per_paper = []
    for p in PAPERS:
        recs = [r for r in records if r["paper_id"] == p]
        per_paper.append(
            {
                "paper_id": p,
                "run_dir": f"research_artifacts_v3/runs/{p.lower()}/",
                "run_files": run_files[p],
                "has_artifacts": run_files[p] >= 1,
                "done": sum(1 for r in recs if r["status"] == "DONE"),
                "blocked": sum(1 for r in recs if r["status"] == "BLOCKED"),
                "human_only": sum(1 for r in recs if r["human_only"]),
                "ledger": (
                    str(TASK_LEDGERS[p][0].relative_to(REPO_ROOT)) if p in TASK_LEDGERS else None
                ),
            }
        )

    global_recs = [r for r in records if r["paper_id"] == "GLOBAL"]
    report = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha": _git_head(),
        "task_register": str(TASK_REGISTER.relative_to(REPO_ROOT)),
        "task_register_sha256": _sha256_file(TASK_REGISTER),
        "rule": (
            "DONE requires machine-readable per-task evidence: a completed status in the "
            "paper's task ledger (DONE/DONE_ENGINEERING/ENGINEERING_PASS/EVIDENCE_VERIFIED/"
            "CODE_READY), all listed evidence paths existing on disk, and a non-empty "
            "research_artifacts_v3/runs/pXX directory. Human-only tasks are always BLOCKED. "
            "Tasks without a task-granular ledger stay BLOCKED (paper-level artifacts do not "
            "prove per-task completion)."
        ),
        "total_tasks": len(records),
        "non_human_tasks": len(non_human),
        "human_only_tasks": len(human_only),
        "by_status": by_status,
        "by_status_non_human": {
            "DONE": sum(1 for r in non_human if r["status"] == "DONE"),
            "BLOCKED": sum(1 for r in non_human if r["status"] == "BLOCKED"),
        },
        "ledger_errors": ledger_errors,
        "violations": violations,
        "papers": per_paper,
        "global_tasks": [
            {k: r[k] for k in ("task_id", "status", "reason")} for r in global_recs
        ],
        "tasks": [
            {k: r.get(k) for k in ("task_id", "paper_id", "human_only", "status", "ledger_status", "reason")}
            for r in records
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rel = args.output.relative_to(REPO_ROOT) if args.output.is_relative_to(REPO_ROOT) else args.output
    print(f"Wrote {rel}")
    print(
        f"Tasks: {len(records)} total | {len(non_human)} non-human | {len(human_only)} human-only"
    )
    print(
        f"Status: {by_status['DONE']} DONE / {by_status['BLOCKED']} BLOCKED "
        f"(non-human: {report['by_status_non_human']['DONE']} DONE / "
        f"{report['by_status_non_human']['BLOCKED']} BLOCKED)"
    )
    print("Per-paper run artifacts:")
    for p in per_paper:
        print(
            f"  {p['paper_id']}: runs={p['run_files']:>3} files | done={p['done']:>2} "
            f"blocked={p['blocked']:>2} human_only={p['human_only']}"
        )
    if ledger_errors:
        print(f"Ledger errors: {ledger_errors}")
    if missing_papers:
        print(f"FAIL: papers without run artifacts: {missing_papers}")
    if violations:
        print("FAIL: human-only tasks marked DONE:")
        for v in violations:
            print(f"  - {v}")
    if missing_papers:
        return 1
    if violations:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
