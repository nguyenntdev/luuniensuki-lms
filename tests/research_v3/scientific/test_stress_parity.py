"""V3-G15/G16/G17: stress suites and parity runner tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v3.datasets.sanitized.generate_stress import (
    FAMILIES,
    generate_ln06_family,
    generate_ln07_family,
    generate_ln09_family,
    write_family,
)
from research_v3.scripts.stress_parity import (
    run_ln06_parity,
    run_ln07_transcript,
    run_ln09_small_cohort,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SANITIZED = REPO_ROOT / "research_v3" / "datasets" / "sanitized"


def test_sanitized_suites_exist_with_manifests_and_do_not_touch_t3():
    t3_snapshots = {}
    for study in ("ln06", "ln07", "ln09"):
        p = REPO_ROOT / "research_v2" / "data" / study / "t3_gold.jsonl"
        t3_snapshots[study] = p.read_bytes() if p.is_file() else None

    for family in FAMILIES:
        manifest_path = SANITIZED / family / "manifest.json"
        assert manifest_path.is_file(), family
        manifest = json.loads(manifest_path.read_text())
        assert manifest["n_cases_total"] == 72
        for f in manifest["files"]:
            data = Path(f["path"]).read_bytes()
            import hashlib

            assert hashlib.sha256(data).hexdigest() == f["sha256"]

    # frozen T3 untouched
    for study, snapshot in t3_snapshots.items():
        p = REPO_ROOT / "research_v2" / "data" / study / "t3_gold.jsonl"
        if snapshot is not None:
            assert p.read_bytes() == snapshot


def test_generators_are_deterministic():
    for gen in (generate_ln06_family, generate_ln07_family, generate_ln09_family):
        assert gen(11) == gen(11)
        assert gen(11)[0]["case_id"] != gen(23)[0]["case_id"]


def test_ln07_suite_has_both_expectation_polarities():
    rows = generate_ln07_family(11)
    labels = {r["label"] for r in rows}
    assert "reject_audio_equivalence" in labels  # positive (failure) cases
    assert "choose_feasible_modality" in labels  # negative (compliant) cases


def test_ln09_suite_has_small_and_large_cohorts():
    rows = generate_ln09_family(11)
    small = [r for r in rows if r["input"]["cohort_size"] < 5]
    large = [r for r in rows if r["input"]["cohort_size"] >= 5]
    assert small and large
    assert all(r["label"] == "descriptive_only" for r in small)
    assert all(r["label"] == "propose_explained_action" for r in large)


def test_parity_runners_pass_on_sealed_suites():
    g15 = run_ln06_parity(11)
    assert g15["status"] == "PASS"
    assert g15["false_infeasibility_rate"] == 0.0

    g16 = run_ln07_transcript(11)
    assert g16["status"] == "SCORED"
    assert g16["n_positive_expectation"] > 0 and g16["n_negative_expectation"] > 0

    g17 = run_ln09_small_cohort(11)
    assert g17["status"] == "PASS"
    assert g17["k_anonymity_divergence_rate"] == 1.0


def test_stress_parity_cli_end_to_end(tmp_path):
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.stress_parity",
         "--seed", "23", "--output", str(tmp_path / "r.json")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    report = json.loads((tmp_path / "r.json").read_text())
    assert {s["status"] for s in report["suites"]} <= {"PASS", "SCORED"}


def test_stress_parity_writes_manifest_hashes(tmp_path):
    manifest = write_family("ln09_small_cohort", (11,), output_dir=tmp_path)
    assert manifest["label_counts"]["descriptive_only"] == 12
    assert manifest["suite_sha256"]
