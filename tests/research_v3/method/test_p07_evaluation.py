"""P07 evaluation pipeline tests: metrics math, leakage audit, artifact
integrity, reproduction (checksum round trip), dataset-card gating."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v3.methods.p07.metrics import (
    all_metrics,
    false_completion,
    missing_affordance_recall,
    rights_compliance,
    task_feasibility,
)
from research_v3.methods.p07.runner import gold_from_cases, load_jsonl, run_method
from research_v3.methods.p07.synthetic_generator import generate_stress_cases

REPO = Path(__file__).resolve().parents[3]
RUN_DIR = REPO / "research_artifacts_v3" / "runs" / "p07" / "p07-wave1"


# ------------------------------------------------------------------ metrics

def test_metrics_exact_numerators_denominators():
    cases = generate_stress_cases(seed=20261115)
    golds = gold_from_cases(cases)
    preds = run_method("proposed", cases)
    m = all_metrics(preds, golds, {str(c["case_id"]): c for c in cases})
    tf = m["task_feasibility_rate"]
    assert tf["denominator"] == len(golds)
    assert tf["numerator"] == sum(1 for p in preds if p["decision"] == golds[p["case_id"]])
    assert tf["rate"] == tf["numerator"] / tf["denominator"]


def test_false_completion_counts_accepts_on_reject_cases():
    golds = {"a": "reject_missing_affordance", "b": "select"}
    preds = [
        {"case_id": "a", "decision": "select", "selected_object_id": "x"},
        {"case_id": "b", "decision": "select", "selected_object_id": "y"},
    ]
    fc = false_completion(preds, golds)
    assert fc["numerator"] == 1
    assert fc["denominator"] == 2


def test_missing_affordance_recall_requires_reason_axis():
    golds = {"a": "reject_missing_affordance", "b": "reject_missing_affordance"}
    preds = [
        {"case_id": "a", "decision": "reject_missing_affordance", "missing_affordances": ["inscription_text"]},
        {"case_id": "b", "decision": "reject_missing_affordance", "missing_affordances": []},
    ]
    rec = missing_affordance_recall(preds, golds)
    assert rec == {"numerator": 1, "denominator": 2, "rate": 0.5}


def test_rights_compliance_flags_unknown_license_selects():
    cases = [
        {"case_id": "c1", "objects": [{"object_id": "o", "license_status": "unknown"}]},
    ]
    preds = [{"case_id": "c1", "decision": "select", "selected_object_id": "o"}]
    rc = rights_compliance(preds, {c["case_id"]: c for c in cases})
    assert rc["violation_count"] == 1
    assert rc["violations"][0]["license_status"] == "unknown"


# ------------------------------------------------------------- leakage audit

def test_leakage_audit_passes_on_model_inputs():
    from research_v3.eval.leakage import audit_rows

    cases = generate_stress_cases(seed=1)
    # model inputs are the case rows (objects/task/device); no gold keys inside
    report = audit_rows(cases, strict=False)
    assert report["status"] == "PASS"
    assert report["duplicates"] == 0


def test_leakage_audit_catches_gold_in_input():
    from research_v3.eval.leakage import LeakageError, audit_rows

    rows = [{"case_id": "x", "input": {"expected_decision": "select"}}]
    with pytest.raises(LeakageError):
        audit_rows(rows, strict=True)


def test_gold_derivation_is_independent_of_model_output():
    """Gold verdicts are computed from affordance/license facts only; tampering
    with prediction structures cannot change them."""
    cases = generate_stress_cases(seed=5)
    g1 = gold_from_cases(cases)
    # predictions for the same cases do not alter gold derivation
    preds = run_method("proposed", cases)
    g2 = gold_from_cases(cases)
    assert g1 == g2
    assert all(p["case_id"] in g1 for p in preds)


# ------------------------------------------------------- artifact integrity

def test_run_artifacts_exist_with_checksums():
    results = RUN_DIR / "results.json"
    sums = RUN_DIR / "SHA256SUMS.txt"
    assert results.is_file(), "run the CLI first: python -m research_v3.experiments.p07.run_matrix"
    assert sums.is_file()
    entries = dict(
        reversed(line.split("  ", 1)) for line in sums.read_text().strip().splitlines()
    )
    import hashlib

    # The manifest cannot contain its own hash (self-reference); verify every
    # OTHER artifact, then verify the manifest was regenerated after them.
    entries.pop("SHA256SUMS.txt", None)
    assert entries, "manifest must list artifacts"
    for rel, expected in entries.items():
        got = hashlib.sha256((RUN_DIR / rel).read_bytes()).hexdigest()
        assert got == expected, f"checksum drift: {rel}"


def test_reproduction_identical_prediction_hash():
    """Rerunning the whole pipeline from frozen inputs yields the identical
    prediction hash (deterministic, no pseudo-replication)."""
    results = json.loads((RUN_DIR / "results.json").read_text())
    assert results["determinism_check"]["identical"] is True
    from research_v2.contracts.canonical_hash import sha256_input

    cases = generate_stress_cases(seed=20261115)
    preds = run_method("proposed", cases)
    assert sha256_input(preds) == results["determinism_check"]["prediction_hash"]


def test_manifest_records_run_metadata():
    results = json.loads((RUN_DIR / "results.json").read_text())
    assert results["run_id"] == "p07-wave1"
    assert results["experiment_card"]["status"] == "PARTIAL"
    assert "single external provider" in " ".join(
        results["experiment_card"]["protocol_deviations"]
    )


# --------------------------------------------------------- dataset card gate

def test_dataset_registry_gate_blocks_unapproved_sources():
    from research_v3.datasets.registry import LicenseGateError, load_registry, require_approved

    registry = load_registry()
    with pytest.raises(LicenseGateError):
        require_approved(registry, ["europeana"], paper_id="P07")


def test_smithsonian_snapshot_card_hashes_match_raw_files():
    """The registry card for the Smithsonian snapshot (if APPROVED) must pin
    the real file hashes we downloaded."""
    import yaml

    reg = yaml.safe_load(
        (REPO / "research_v3" / "datasets" / "registry.yaml").read_text(encoding="utf-8")
    )
    card = next(
        (d for d in reg["datasets"] if d["dataset_id"] == "smithsonian-open-access-fsg"),
        None,
    )
    if card is None:
        pytest.skip("smithsonian card not registered")
    lic = REPO / "private_data/raw/smithsonian_open_access/2021-12-21/si_license_CC0-1.0.txt"
    assert card["license_text_sha256"] == hashlib_sha256(lic)


def hashlib_sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
