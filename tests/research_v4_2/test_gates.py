"""Comprehensive test suite for Research V4.2 Science and Release Gates.

Tests all 8 automated release gates with both valid (PASS) scenarios and
negative falsification canaries (FAIL). Also tests contract cards, canonical JSON hashing,
and CLI entrypoints.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import pytest

from research_v4_2.contracts import (
    ClaimStatus,
    WinType,
    PublicationGrade,
    DatasetCard,
    BaselineCard,
    FailureCard,
    NoveltyCard,
    MethodCard,
    WinCard,
    canonical_hash,
)
from research_v4_2.gates import (
    validate_test_exit,
    validate_preregistration,
    validate_novelty,
    validate_baseline_parity,
    validate_statistical_claims,
    validate_integrity,
    validate_license_ethics,
    validate_cross_paper_independence,
)


# ============================================================================
# Gate 1: test_exit Tests
# ============================================================================

def test_test_exit_clean_pass():
    """Verify that a clean test run with exit code 0 and passing log passes."""
    log = "======================== 15 passed in 1.23s ========================"
    res = validate_test_exit(exit_code=0, log_content=log)
    assert res.passed is True
    assert "verified clean" in res.messages[0]


def test_test_exit_nonzero_fail():
    """Negative Canary: Non-zero exit code must fail immediately."""
    res = validate_test_exit(exit_code=1, log_content="")
    assert res.passed is False
    assert any("non-zero exit code" in m for m in res.messages)


def test_test_exit_masked_failure_in_log():
    """Negative Canary: Exit code 0 with failures in log (piped failure) must be caught."""
    log = "FAILED tests/test_foo.py::test_bar\n=== 1 failed, 14 passed in 2.10s ==="
    res = validate_test_exit(exit_code=0, log_content=log)
    assert res.passed is False
    assert any("MASKED_TEST_FAILURE" in m for m in res.messages)


# ============================================================================
# Gate 2: preregister Tests
# ============================================================================

@pytest.fixture
def sample_prereg():
    return {
        "claim_id": "CLM-P01-01",
        "paper_id": "P01",
        "primary_metric": "aurc",
        "delta_min": 0.02,
        "baseline_champion_id": "C2_CRC_CONFORMAL",
        "method_code_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "frozen_at": "2026-11-18T10:00:00Z",
    }


def test_preregister_valid_pass(sample_prereg):
    """Verify that matching preregistration and WinCard pass."""
    prereg_sha = canonical_hash(sample_prereg)
    win_card = {
        "prereg_sha256": prereg_sha,
        "baseline_champion_id": "C2_CRC_CONFORMAL",
        "primary_metric": "aurc",
        "delta_min": 0.02,
        "test_completed_at": "2026-11-19T10:00:00Z",
    }
    method_card = {
        "code_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    }
    res = validate_preregistration(sample_prereg, win_card, method_card)
    assert res.passed is True


def test_preregister_tampered_hash_fail(sample_prereg):
    """Negative Canary: Preregistration content modification detected by hash mismatch."""
    win_card = {
        "prereg_sha256": "stale_or_wrong_hash",
        "baseline_champion_id": "C2_CRC_CONFORMAL",
        "primary_metric": "aurc",
        "delta_min": 0.02,
    }
    res = validate_preregistration(sample_prereg, win_card)
    assert res.passed is False
    assert any("PREREG_HASH_MISMATCH" in m for m in res.messages)


def test_preregister_champion_swap_fail(sample_prereg):
    """Negative Canary: Changing baseline champion after preregistration must fail."""
    prereg_sha = canonical_hash(sample_prereg)
    win_card = {
        "prereg_sha256": prereg_sha,
        "baseline_champion_id": "C1_WEAKER_BASELINE",
        "primary_metric": "aurc",
        "delta_min": 0.02,
    }
    res = validate_preregistration(sample_prereg, win_card)
    assert res.passed is False
    assert any("CHAMPION_CHANGED_POST_HOC" in m for m in res.messages)


def test_preregister_delta_min_relaxed_fail(sample_prereg):
    """Negative Canary: Relaxing delta_min post-hoc must fail."""
    prereg_sha = canonical_hash(sample_prereg)
    win_card = {
        "prereg_sha256": prereg_sha,
        "baseline_champion_id": "C2_CRC_CONFORMAL",
        "primary_metric": "aurc",
        "delta_min": 0.005,  # Relaxed from 0.02
    }
    res = validate_preregistration(sample_prereg, win_card)
    assert res.passed is False
    assert any("DELTA_MIN_RELAXED" in m for m in res.messages)


def test_preregister_method_mutation_fail(sample_prereg):
    """Negative Canary: Modifying method code after preregistration freeze must fail."""
    prereg_sha = canonical_hash(sample_prereg)
    win_card = {
        "prereg_sha256": prereg_sha,
        "baseline_champion_id": "C2_CRC_CONFORMAL",
        "primary_metric": "aurc",
        "delta_min": 0.02,
    }
    method_card = {"code_sha256": "modified_post_test_code_hash"}
    res = validate_preregistration(sample_prereg, win_card, method_card)
    assert res.passed is False
    assert any("POSTTEST_METHOD_HASH_MUTATION" in m for m in res.messages)


# ============================================================================
# Gate 3: novelty Tests
# ============================================================================

@pytest.fixture
def sample_novelty_card():
    return {
        "novelty_card_id": "NOV-P01",
        "paper_id": "P01",
        "closest_works": [
            {"title": "Cost-aware conformal prediction", "citation_or_doi": "doi:10.1234/uai2026", "overlap": "Conformal deferral"},
            {"title": "Selective Classification with Neural Networks", "citation_or_doi": "doi:10.1234/icml2017", "overlap": "Risk-coverage trade-off"},
            {"title": "Early warning student risk transfer", "citation_or_doi": "doi:10.1234/edm2023", "overlap": "Student risk scoring"},
        ],
        "direct_overlaps": ["Conformal risk control thresholding", "Selective deferral to teacher review"],
        "formal_counterexample": "Prior cost-aware conformal methods fail when reviewer queue capacity is strictly sub-linear with arrival shifts.",
        "n1_to_n7_criteria": {f"N{i}": True for i in range(1, 8)},
        "independent_human_signoff": {
            "signed": True,
            "reviewer": "Dr. Le Van Khoa (Senior AI Heritage Fellow)",
            "date": "2026-11-19",
            "affiliation": "Vietnam National University",
        },
    }


def test_novelty_valid_pass(sample_novelty_card):
    """Verify that a complete NoveltyCard with human signoff passes."""
    res = validate_novelty(sample_novelty_card)
    assert res.passed is True


def test_novelty_fewer_than_3_works_fail(sample_novelty_card):
    """Negative Canary: Fewer than 3 closest works must fail."""
    sample_novelty_card["closest_works"] = sample_novelty_card["closest_works"][:2]
    res = validate_novelty(sample_novelty_card)
    assert res.passed is False
    assert any("INSUFFICIENT_PRIOR_ART" in m for m in res.messages)


def test_novelty_missing_human_signoff_fail(sample_novelty_card):
    """Negative Canary: Missing human signoff blocks release (no auto-novelty pass)."""
    sample_novelty_card["independent_human_signoff"] = None
    res = validate_novelty(sample_novelty_card)
    assert res.passed is False
    assert any("HUMAN_SIGNOFF_BLOCKED" in m for m in res.messages)


def test_novelty_human_signoff_unsigned_fail(sample_novelty_card):
    """Negative Canary: Human signoff with signed=False must fail."""
    sample_novelty_card["independent_human_signoff"]["signed"] = False
    res = validate_novelty(sample_novelty_card)
    assert res.passed is False
    assert any("HUMAN_SIGNOFF_NOT_SIGNED" in m for m in res.messages)


# ============================================================================
# Gate 4: baseline_parity Tests
# ============================================================================

@pytest.fixture
def sample_split_data():
    cand = [{"case_id": f"c_{i}", "y_pred": 1, "covered": True} for i in range(50)]
    base = [{"case_id": f"c_{i}", "y_pred": 0, "covered": True} for i in range(50)]
    gold = [{"case_id": f"c_{i}", "y_true": 1} for i in range(50)]
    return cand, base, gold


def test_baseline_parity_valid_pass(sample_split_data):
    """Verify aligned candidate, baseline, and gold pass."""
    cand, base, gold = sample_split_data
    res = validate_baseline_parity(cand, base, gold)
    assert res.passed is True


def test_baseline_parity_denominator_mismatch_fail(sample_split_data):
    """Negative Canary: Different test sizes must fail."""
    cand, base, gold = sample_split_data
    res = validate_baseline_parity(cand[:40], base, gold)
    assert res.passed is False
    assert any("DENOMINATOR_MISMATCH" in m for m in res.messages)


def test_baseline_parity_case_id_mismatch_fail(sample_split_data):
    """Negative Canary: Mismatched case IDs must fail."""
    cand, base, gold = sample_split_data
    cand_alt = [{"case_id": f"diff_{i}", "y_pred": 1, "covered": True} for i in range(50)]
    res = validate_baseline_parity(cand_alt, base, gold)
    assert res.passed is False
    assert any("CASE_ID_MISMATCH" in m for m in res.messages)


def test_baseline_parity_train_test_leakage_fail(sample_split_data):
    """Negative Canary: Test IDs found in training split must fail."""
    cand, base, gold = sample_split_data
    train_records = [{"case_id": "c_5"}, {"case_id": "c_999"}]
    res = validate_baseline_parity(cand, base, gold, train_records=train_records)
    assert res.passed is False
    assert any("DATASET_LEAKAGE_DETECTED" in m for m in res.messages)


# ============================================================================
# Gate 5: statistical_claims Tests
# ============================================================================

def test_statistical_claims_valid_pass():
    """Verify that a genuine superior candidate with CI > 0 and p_adj < 0.05 passes."""
    n = 60
    # Candidate gets 90% accuracy, Baseline gets 60% accuracy, cluster size = 6 (10 clusters)
    gold = [{"case_id": i, "cluster_id": f"cl_{i // 6}", "y_true": 1} for i in range(n)]
    cand = [{"case_id": i, "cluster_id": f"cl_{i // 6}", "y_pred": 1} for i in range(n)]
    base = [{"case_id": i, "cluster_id": f"cl_{i // 6}", "y_pred": 1 if i % 3 != 0 else 0} for i in range(n)]

    # Candidate acc = 1.0, baseline acc ~ 0.6667, delta ~ 0.3333
    win_card = {
        "primary_metric": "accuracy",
        "delta_min": 0.05,
        "effect": 0.3333,
        "ci95": [0.20, 0.45],
        "p_raw": 0.001,
        "p_adjusted": 0.002,
    }
    res = validate_statistical_claims(win_card, cand, base, gold, cluster_key="cluster_id", tolerance=0.02)
    assert res.passed is True


def test_statistical_claims_delta_below_min_fail():
    """Negative Canary: Delta lower than preregistered minimum delta_min must fail."""
    n = 50
    gold = [{"case_id": i, "cluster_id": f"cl_{i // 5}", "y_true": 1} for i in range(n)]
    cand = [{"case_id": i, "cluster_id": f"cl_{i // 5}", "y_pred": 1} for i in range(n)]
    base = [{"case_id": i, "cluster_id": f"cl_{i // 5}", "y_pred": 1} for i in range(n)]  # Identical, delta = 0

    win_card = {
        "primary_metric": "accuracy",
        "delta_min": 0.05,
        "effect": 0.0,
        "ci95": [0.0, 0.0],
        "p_adjusted": 1.0,
    }
    res = validate_statistical_claims(win_card, cand, base, gold)
    assert res.passed is False
    assert any("DELTA_BELOW_MINIMUM" in m for m in res.messages)


def test_statistical_claims_underpowered_fail():
    """Negative Canary: Dataset with small sample size (n < 30) must be rejected."""
    n = 10  # Insufficient instances
    gold = [{"case_id": i, "cluster_id": f"cl_{i}", "y_true": 1} for i in range(n)]
    cand = [{"case_id": i, "cluster_id": f"cl_{i}", "y_pred": 1} for i in range(n)]
    base = [{"case_id": i, "cluster_id": f"cl_{i}", "y_pred": 0} for i in range(n)]

    win_card = {
        "primary_metric": "accuracy",
        "delta_min": 0.05,
        "effect": 1.0,
        "ci95": [0.8, 1.0],
        "p_adjusted": 0.01,
    }
    res = validate_statistical_claims(win_card, cand, base, gold)
    assert res.passed is False
    assert any("UNDERPOWERED_CLAIM" in m for m in res.messages)


# ============================================================================
# Gate 6: integrity Tests
# ============================================================================

def test_integrity_valid_pass():
    """Verify valid signed cards and portable paths pass integrity checks."""
    card = MethodCard(
        method_id="MTH-01",
        paper_id="P01",
        objective="Minimize selective risk under capacity constraint",
        complexity="O(N log N)",
    )
    card.sign_hash()
    assert card.verify_hash() is True

    receipts = [
        {"split": "train", "model_id": "v1"},
        {"split": "dev", "model_id": "v1"},
        {"split": "test", "model_id": "v1"},
    ]

    res = validate_integrity(card_objects=[card.model_dump()], test_receipts=receipts)
    assert res.passed is True


def test_integrity_tampered_card_fail():
    """Negative Canary: Tampered card content without updating hash must fail."""
    card = MethodCard(method_id="MTH-01", paper_id="P01", objective="Original")
    card.sign_hash()
    card_dict = card.model_dump()
    card_dict["objective"] = "Tampered objective post-sign"

    res = validate_integrity(card_objects=[card_dict])
    assert res.passed is False
    assert any("CARD_SHA_MISMATCH" in m for m in res.messages)


def test_integrity_non_portable_path_fail():
    """Negative Canary: Machine-specific absolute path (/home/clue) must fail."""
    card = DatasetCard(
        dataset_id="DS-01",
        paper_id="P01",
        file_hashes={"raw": "abc"},
        rights_and_license={"path": "/home/clue/secret/data.csv", "license": "MIT"},
    )
    card.sign_hash()
    res = validate_integrity(card_objects=[card.model_dump()])
    assert res.passed is False
    assert any("NON_PORTABLE_PATH_DETECTED" in m for m in res.messages)


def test_integrity_duplicate_test_trials_fail():
    """Negative Canary: Multiple test runs with different model configurations must fail."""
    receipts = [
        {"split": "test", "model_id": "model_candidate_A"},
        {"split": "test", "model_id": "model_candidate_B"},
    ]
    res = validate_integrity(card_objects=[], test_receipts=receipts)
    assert res.passed is False
    assert any("DUPLICATE_TEST_TRIAL_DETECTED" in m for m in res.messages)


# ============================================================================
# Gate 7: license_ethics Tests
# ============================================================================

def test_license_ethics_valid_pass():
    """Verify open licensed dataset with IRB ethics clearance passes."""
    ds = {
        "dataset_id": "student_assessment_v1",
        "task_ontology": {"task": "learner_scoring", "participants": "students"},
        "rights_and_license": {"license": "CC-BY-4.0"},
        "ethics_clearance": {
            "cleared": True,
            "protocol_id": "IRB-2026-VNU-042",
            "committee": "Institutional Review Board",
        },
    }
    base = [{"baseline_id": "pykt_baseline", "license": "MIT"}]
    res = validate_license_ethics(ds, base)
    assert res.passed is True


def test_license_ethics_heritage_archive_authorization():
    """Verify authorized historical records (Châu bản triều Nguyễn) are approved."""
    ds = {
        "dataset_id": "chau_ban_trieu_nguyen_epigraphy",
        "task_ontology": {"task": "historical_ocr", "source": "Đại Nam thực lục triều Nguyễn"},
        "rights_and_license": {
            "license": "Nguyen Dynasty Imperial Archives Research Excerpt",
            "authorized_heritage_source": True,
        },
    }
    res = validate_license_ethics(ds)
    assert res.passed is True
    assert res.details.get("heritage_archive_authorization") == "AUTHORIZED_IMPERIAL_ARCHIVE_RESEARCH_SOURCE"


def test_license_ethics_missing_ethics_fail():
    """Negative Canary: Dataset with human students without ethics clearance must fail."""
    ds = {
        "dataset_id": "student_clickstream",
        "task_ontology": {"task": "student_dropout_prediction"},
        "rights_and_license": {"license": "MIT"},
        "ethics_clearance": None,  # Missing
    }
    res = validate_license_ethics(ds)
    assert res.passed is False
    assert any("ETHICS_CLEARANCE_MISSING" in m for m in res.messages)


def test_license_ethics_unapproved_baseline_license_fail():
    """Negative Canary: Baseline with proprietary/unapproved license must fail."""
    ds = {"dataset_id": "benchmark_data", "rights_and_license": {"license": "CC0"}}
    base = [{"baseline_id": "closed_proprietary_tool", "license": "Proprietary Commercial Closed Source"}]
    res = validate_license_ethics(ds, base)
    assert res.passed is False
    assert any("UNAPPROVED_BASELINE_LICENSE" in m for m in res.messages)


# ============================================================================
# Gate 8: cross_paper Tests
# ============================================================================

def test_cross_paper_independence_valid_pass():
    """Verify distinct papers with independent estimands pass."""
    cards = [
        {"paper_id": "P01", "claim_id": "CLM-P01", "estimand": "selective_learner_risk", "primary_metric": "aurc"},
        {"paper_id": "P02", "claim_id": "CLM-P02", "estimand": "exact_itinerary_planning", "primary_metric": "p95_latency"},
        {"paper_id": "P07", "claim_id": "CLM-P07", "estimand": "rights_constrained_multimedia_knapsack", "primary_metric": "ndcg"},
        {"paper_id": "P14", "claim_id": "CLM-P14", "estimand": "heritage_semantic_alt_text_accessibility", "primary_metric": "recall"},
        {"paper_id": "P09", "claim_id": "CLM-P09", "estimand": "primary_source_evidence_retrieval", "primary_metric": "grounded_f1"},
        {"paper_id": "P12", "claim_id": "CLM-P12", "estimand": "locator_level_archival_tamper_detection", "primary_metric": "detection_rate"},
    ]
    res = validate_cross_paper_independence(cards)
    assert res.passed is True


def test_cross_paper_duplicate_estimand_fail():
    """Negative Canary: Two papers claiming identical estimand must fail."""
    cards = [
        {"paper_id": "P01", "claim_id": "CLM-01", "estimand": "student_dropout_prediction", "primary_metric": "auc"},
        {"paper_id": "P05", "claim_id": "CLM-02", "estimand": "student_dropout_prediction", "primary_metric": "auc"},
    ]
    res = validate_cross_paper_independence(cards)
    assert res.passed is False
    assert any("DUPLICATE_ESTIMAND_COLLISION" in m for m in res.messages)


def test_cross_paper_p09_p12_collision_fail():
    """Negative Canary: P09 and P12 sharing identical estimand must be flagged."""
    cards = [
        {"paper_id": "P09", "claim_id": "CLM-P09", "estimand": "archival_grounding", "primary_metric": "f1"},
        {"paper_id": "P12", "claim_id": "CLM-P12", "estimand": "archival_grounding", "primary_metric": "f1"},
    ]
    res = validate_cross_paper_independence(cards)
    assert res.passed is False
    assert any("P09_P12_COLLISION" in m for m in res.messages)


# ============================================================================
# CLI Entrypoints Test
# ============================================================================

def test_cli_entrypoints():
    """Verify that all 8 gate modules can be invoked via `python -m research_v4_2.gates.<gate> --help`."""
    gate_modules = [
        "test_exit",
        "preregister",
        "novelty",
        "baseline_parity",
        "statistical_claims",
        "integrity",
        "license_ethics",
        "cross_paper",
    ]
    for g in gate_modules:
        cmd = [sys.executable, "-m", f"research_v4_2.gates.{g}", "--help"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI help failed for {g}: {proc.stderr}"
