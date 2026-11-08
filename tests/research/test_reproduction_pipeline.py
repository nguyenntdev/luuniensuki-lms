# -*- coding: utf-8 -*-
"""Comprehensive unit tests for the research reproduction pipeline.

Verifies:
1. Automated clean environment checking and baseline ancestry validation.
2. Self-contained fixture integrity and source checking without external spec paths.
3. Smoke execution of benchmark runs with artifact verification.
4. Independent holdout evaluations across studies.
5. Statistical significance metric computation (McNemar, ARR, RRR, contingency tables).
6. Publication table generation and release readiness verification.
7. Full CLI interface execution of reproduce_all.py.
8. Guarantee that executing the reproduction pipeline does not dirty the git state.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any, Dict

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RESEARCH_TOOLS = REPO_ROOT / "research" / "tools"
if str(RESEARCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_TOOLS))

from check_sources import verify_spec
from recompute_metrics import compute
from reproduce_all import (
    check_clean_environment,
    compute_statistical_significance,
    mcnemar_test,
    paired_proportion_ci95,
    run_benchmark_matrix,
    run_holdout_evaluations,
    verify_and_generate_tables,
)
from verify_release import check as verify_release_check


def test_clean_environment_check():
    """Verify clean environment check correctly validates git ancestry, python, and fixtures."""
    env_info = check_clean_environment(REPO_ROOT, allow_uncommitted=True)
    assert env_info["status"] == "PASS", f"Environment check failed: {env_info.get('problems')}"
    assert env_info["fixtures_validated"] == 10
    assert env_info["holdout_files_present"] == 10
    assert env_info["adapters_imported"] == 10
    assert env_info["ancestral_baseline"] == "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
    assert env_info["head_sha"] != "unknown"


def test_check_sources_self_contained():
    """Verify check_sources operates self-contained on repo fixtures without external spec dir."""
    fixtures_dir = REPO_ROOT / "research" / "fixtures"
    res = verify_spec(fixtures_dir)
    assert not res["issues"], f"Issues found in self-contained fixtures: {res['issues']}"
    assert len(res["stats"]["fixtures"]) == 10
    for study, f_stat in res["stats"]["fixtures"].items():
        assert f_stat["rows"] == 720
        assert sum(f_stat["faults"].values()) == 720
        assert len(f_stat["faults"]) == 5
        assert all(count == 144 for count in f_stat["faults"].values())


def test_statistical_math_helpers():
    """Verify McNemar test and confidence interval calculations."""
    # When both conditions agree, chi2=0, p=1
    chi2, p_val = mcnemar_test(0, 0)
    assert chi2 == 0.0
    assert p_val == 1.0

    # Discordant pairs (e.g. 50 baseline failures fixed, 0 regressions)
    chi2, p_val = mcnemar_test(50, 0)
    assert chi2 > 40.0
    assert p_val < 1e-10

    # Paired proportion CI
    low, high = paired_proportion_ci95(1.0, 0.0, 50, 0, 50)
    assert low <= 1.0 <= high


def test_benchmark_matrix_smoke_execution(tmp_path: pathlib.Path):
    """Execute smoke benchmark matrix on LN-01 with max_cases=5 into temporary directory."""
    bm_out = tmp_path / "benchmark"
    report = run_benchmark_matrix(
        repo=REPO_ROOT,
        benchmark_dir=bm_out,
        workers=2,
        studies="LN-01",
        allow_uncommitted=True,
        max_cases=5,
    )
    assert report["status"] == "PASS"
    assert len(report["results"]) == 1
    assert report["results"][0]["study"] == "LN-01"
    assert report["results"][0]["conditions"] == 5

    # Check required artifact files in each condition
    for cond in ["B0", "I1", "A1", "A2", "A3"]:
        cond_dir = bm_out / "LN-01" / cond
        assert cond_dir.is_dir()
        assert (cond_dir / "trace.jsonl").is_file()
        assert (cond_dir / "manifest.json").is_file()
        assert (cond_dir / "study_metric.json").is_file()
        assert (cond_dir / "config.json").is_file()
        assert (cond_dir / "execution_log.txt").is_file()

        # Check trace lines count
        trace_lines = (cond_dir / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(trace_lines) == 5

        # Check manifest
        manifest = json.loads((cond_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["paper_id"] == "LN-01"
        assert manifest["cases_run"] == 5
        assert manifest["adapter_errors"] == 0


def test_holdout_evaluations(tmp_path: pathlib.Path):
    """Evaluate independent holdouts for LN-01 and LN-02 into temporary directory."""
    ho_out = tmp_path / "holdout"
    report = run_holdout_evaluations(
        holdout_out_dir=ho_out,
        studies_filter="LN-01,LN-02",
    )
    assert report["status"] == "PASS"
    assert report["studies_evaluated"] == 2
    assert report["total_cases"] == 240
    assert (ho_out / "holdout_evaluation_report.json").is_file()
    assert (ho_out / "holdout_summary.csv").is_file()

    for r in report["results"]:
        assert r["status"] == "PASS"
        assert r["cases_evaluated"] == 120
        assert r["intervention_accuracy"] >= 0.95
        assert r["accuracy_gain"] > 0.0


def test_statistical_significance_computation(tmp_path: pathlib.Path):
    """Compute statistical significance metrics from validated research_artifacts."""
    stats_out = tmp_path / "statistics"
    report = compute_statistical_significance(
        benchmark_dir=REPO_ROOT / "research_artifacts",
        stats_out_dir=stats_out,
        studies_filter="LN-01,LN-02,LN-03",
    )
    assert report["studies_analyzed"] == 3
    assert (stats_out / "statistical_significance_report.json").is_file()
    assert (stats_out / "statistical_summary.csv").is_file()

    for item in report["results"]:
        assert item["eligible_n"] > 0
        assert item["baseline_rate"] > item["intervention_rate"]
        assert item["absolute_risk_reduction"] > 0.0
        assert item["mcnemar_chi2"] > 0.0
        assert item["mcnemar_p_value"] < 0.001
        assert item["statistically_significant_p001"] is True
        contingency = item["contingency_table"]
        assert "both_pass" in contingency
        assert "baseline_fail_intervention_pass" in contingency


def test_verify_release_and_tables(tmp_path: pathlib.Path):
    """Verify release readiness on research_artifacts and generate LaTeX/CSV tables."""
    tables_out = tmp_path / "manuscript_tables"
    result = verify_and_generate_tables(
        benchmark_dir=REPO_ROOT / "research_artifacts",
        tables_dir=tables_out,
    )
    rel_val = result["release_validation"]
    assert rel_val["status"] == "SOFTWARE_EVIDENCE_TECHNICALLY_COMPLETE"
    assert rel_val["verified_runs"] == 50
    assert len(rel_val["blockers"]) == 0

    # Verify tables generated for all 10 studies
    for i in range(1, 11):
        study = f"LN-{i:02d}"
        tex_file = tables_out / f"{study}_results.tex"
        csv_file = tables_out / f"{study}_results.csv"
        assert tex_file.is_file(), f"Missing {tex_file}"
        assert csv_file.is_file(), f"Missing {csv_file}"
        tex_content = tex_file.read_text(encoding="utf-8")
        assert r"\begin{table}" in tex_content
        assert r"\end{table}" in tex_content


def test_full_cli_reproduce_all(tmp_path: pathlib.Path):
    """Invoke CLI reproduction script via subprocess with JSON output."""
    cli_out = tmp_path / "cli_run"
    cmd = [
        sys.executable,
        str(RESEARCH_TOOLS / "reproduce_all.py"),
        "--holdout",
        "--statistics",
        "--verify",
        "--output",
        str(cli_out),
        "--studies",
        "LN-01",
        "--allow-uncommitted",
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"CLI command failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    payload = json.loads(proc.stdout)
    assert payload["overall_status"] == "PASS"
    assert "environment_check" in payload["phases"]
    assert "holdout" in payload["phases"]
    assert "statistics" in payload["phases"]
    assert "verification" in payload["phases"]


def test_git_state_unmodified(tmp_path: pathlib.Path):
    """Verify that running the reproduction pipeline does not dirty the git state."""
    # Capture porcelain status before running
    before_status = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    # Run reproduction suite in isolated tmp_path
    sub_out = tmp_path / "isolated_run"
    cmd = [
        sys.executable,
        str(RESEARCH_TOOLS / "reproduce_all.py"),
        "--holdout",
        "--statistics",
        "--output",
        str(sub_out),
        "--studies",
        "LN-01",
        "--allow-uncommitted",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Reproduction run failed: {res.stderr}"

    # Capture porcelain status after running
    after_status = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    # Must be strictly identical
    assert before_status == after_status, "Git working tree was dirtied by running reproduction pipeline!"
