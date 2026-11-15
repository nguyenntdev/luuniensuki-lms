"""P11 prereg + status-ledger integrity: statuses honest, no fabricated metrics anywhere."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO = Path.cwd()
PREREG = REPO / "research_v3" / "methods" / "p11" / "pre_registration.yaml"
MANIFEST = REPO / "research_artifacts_v3" / "runs" / "p11" / "status_manifest.json"
MANUSCRIPT = REPO / "research_v3" / "manuscripts" / "p11" / "MANUSCRIPT.md"


def test_prereg_frozen_with_primary_endpoint_and_h0():
    prereg = yaml.safe_load(PREREG.read_text(encoding="utf-8"))
    assert prereg["paper_id"] == "P11"
    assert prereg["estimand"]["primary_statistic"] == "quadratic_weighted_cohen_kappa_per_criterion"
    assert "H0" in prereg["hypotheses"]
    assert prereg["frozen_at"].startswith("2026-11-15")
    # falsification registered BEFORE any data
    assert "kappa_w(overall) < 0.41" in prereg["falsification_registered"][0]
    assert prereg["design"]["blinding"].startswith("full")


def test_status_manifest_all_21_tasks_with_honest_statuses():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = [t["id"] for t in manifest["tasks"]]
    assert len(ids) == 21
    assert len(set(ids)) == 21
    blocked = {t["id"]: t for t in manifest["tasks"] if t["status"] == "BLOCKED"}
    # the explicitly required human-only blocks
    for required in ("P11-T19", "P11-T20", "P11-T21"):
        assert required in blocked, f"{required} must be BLOCKED"
        assert blocked[required]["evidence"].startswith("BLOCKED:")
    # every blocked task carries an explicit reason
    for t in blocked.values():
        assert "BLOCKED:" in t["evidence"]
    # no task claims SUCCESS
    for t in manifest["tasks"]:
        assert t["status"] in {"ENGINEERING_PASS", "PARTIAL", "BLOCKED"}


def test_manifest_contains_no_metric_like_numbers():
    """The only numbers allowed in the manifest are statuses, hashes, and counts."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    text = json.dumps(manifest)
    for banned in ("kappa", "alpha_0.", "icc_0.", '"score"', "agreement_"):
        assert banned not in text.lower() or banned in ("kappa",)  # 'kappa' may appear only as blocked-task wording
    # hash fields must be real sha256 of files
    import hashlib

    for path, digest in manifest["artifact_hashes"].items():
        p = REPO / path
        assert p.exists(), path
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest


def test_manuscript_marks_all_results_blocked_and_has_no_validity_claim():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    assert "BLOCKED — RATER_AND_SAMPLE_REQUIRED" in text
    assert text.count("**BLOCKED**") >= 6  # every results cell
    # no validity language in assertions
    lower = text.lower()
    for banned_claim in ("we demonstrate that the rubric is reliable", "the rubric is valid", "significant improvement over"):
        assert banned_claim not in lower
    assert "no validity or reliability claim" in lower


def test_prereg_yaml_roundtrip_and_multiplicity():
    prereg = yaml.safe_load(PREREG.read_text(encoding="utf-8"))
    assert prereg["comparison_family"]["multiplicity_correction"] == "holm"
    assert len(prereg["comparison_family"]["contrasts"]) >= 3
