"""Tests for Paper P07: Resource- and Rights-Aware Multimedia Selection (V4.2)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import yaml
import pytest

from research_v4_2.papers.p07.baselines import C0UrlPresent, C1StaticFallback, C2SigLIP2GreedyReranker
from research_v4_2.papers.p07.experiment import run_benchmark, write_all_receipts
from research_v4_2.papers.p07.method import (
    ALLOWED_LICENSES,
    DeviceProfile,
    LearningObject,
    RightsAwareILPSelector,
    TaskSpec,
)


@pytest.fixture
def p07_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "research_v4_2" / "papers" / "p07"


def test_p07_all_12_artifacts_exist_and_validate(p07_dir: Path):
    """Verifies that all 12 artifact receipts exist and contain valid fields."""
    write_all_receipts(p07_dir)

    expected_files = [
        "00_v3_case_reproduction.json",
        "01_prior_art_screen.csv",
        "02_baseline_champion_manifest.json",
        "03_residual_failures.jsonl",
        "04_novelty_counterexample.md",
        "05_method_theory_and_complexity.md",
        "06_dev_trials_append_only.jsonl",
        "07_ablation_and_canary_results.json",
        "08_preregistration.lock.yaml",
        "09_confirmatory_receipt.json",
        "10_replication_receipt.json",
        "11_claim_clearance.json",
    ]

    for fname in expected_files:
        fpath = p07_dir / fname
        assert fpath.exists(), f"Missing artifact receipt: {fname}"
        assert fpath.stat().st_size > 0, f"Empty artifact receipt: {fname}"

    # Validate 09_confirmatory_receipt.json
    conf = json.loads((p07_dir / "09_confirmatory_receipt.json").read_text())
    assert conf["paper_id"] == "P07"
    assert conf["delta"] >= conf["delta_min"]
    assert conf["ci95"][0] > 0
    assert conf["p_adjusted"] < 0.05
    assert conf["win_condition_satisfied"] is True
    assert conf["false_permission_rate"] == 0.0

    # Validate 08_preregistration.lock.yaml
    prereg = yaml.safe_load((p07_dir / "08_preregistration.lock.yaml").read_text())
    assert prereg["primary_metric"] == "rights_valid_utility"
    assert prereg["delta_min"] == 0.15

    # Validate 11_claim_clearance.json
    clearance = json.loads((p07_dir / "11_claim_clearance.json").read_text())
    assert clearance["claim_status"] == "ENGINEERING_ONLY"
    assert clearance["human_approval"] is False


def test_p07_candidate_beats_baseline_champion():
    """Confirms that proposed RAC-ILP beats baseline champion B* by margin >= delta_min."""
    results = run_benchmark()
    b_star = results["baseline_champion"]
    delta = results["delta"]
    assert delta >= 0.15, f"Delta {delta} did not meet minimum threshold 0.15"
    assert results["ci95"][0] > 0, f"CI lower bound {results['ci95'][0]} must be > 0"
    assert results["p_adjusted"] < 0.05, f"Adjusted p-value {results['p_adjusted']} must be < 0.05"
    assert results["false_permission_rates"]["proposed"] == 0.0, "Proposed method must have 0 false permissions"


def test_p07_rights_and_device_invariants():
    """Verifies hard invariants: never select copyrighted or unfeasible objects."""
    selector = RightsAwareILPSelector()
    task = TaskSpec(task_id="T1", required_affordances=("inscription_text", "visual_inspection"))
    device = DeviceProfile(max_payload_kb=200, network_kbps=100, webgl=False)

    # Candidate 1: High relevance but copyrighted
    c1 = LearningObject(
        object_id="O1",
        modality="2d_rubbing",
        license_status="AllRightsReserved",
        kb=100,
        affordances={"inscription_text": True, "visual_inspection": True},
        semantic_relevance=0.99,
        provenance_verified=False,
    )
    # Candidate 2: 3D mesh requiring WebGL and 800 KB (both infeasible)
    c2 = LearningObject(
        object_id="O2",
        modality="3d",
        license_status="CC0-1.0",
        kb=800,
        affordances={"inscription_text": True, "visual_inspection": True},
        semantic_relevance=0.95,
        provenance_verified=True,
    )

    decision = selector.select(task, device, [c1, c2])
    # Must reject both; never serve c1 or c2
    assert decision.status in ("reject_rights_violation", "reject_device_infeasible")
    assert decision.selected_object_id is None
    assert decision.utility == 0.0


def test_p07_negative_canary_abstention_on_missing_affordance():
    """Negative canary: When no candidate affords the required task, must abstain cleanly."""
    selector = RightsAwareILPSelector()
    task = TaskSpec(task_id="T2", required_affordances=("inscription_text", "relief_depth"))
    device = DeviceProfile(max_payload_kb=500, network_kbps=300, webgl=True)

    # Object has valid rights and is feasible, but lacks relief_depth
    c = LearningObject(
        object_id="O3",
        modality="2d_image",
        license_status="CC0-1.0",
        kb=100,
        affordances={"inscription_text": True, "relief_depth": False},
        semantic_relevance=0.90,
        provenance_verified=True,
    )

    decision = selector.select(task, device, [c])
    assert decision.status == "abstain_missing_affordance"
    assert "relief_depth" in decision.missing_affordances
    assert decision.selected_object_id is None


def test_p07_determinism():
    """Verifies identical inputs produce identical outputs (no RNG / wall-clock leakage)."""
    selector = RightsAwareILPSelector()
    task = TaskSpec(task_id="T3", required_affordances=("visual_inspection",))
    device = DeviceProfile(max_payload_kb=500, network_kbps=300)
    candidates = [
        LearningObject("O1", "2d_image", "CC0-1.0", 120, {"visual_inspection": True}, 0.85, True),
        LearningObject("O2", "2d_rubbing", "CC-BY-4.0", 90, {"visual_inspection": True}, 0.85, True),
    ]

    d1 = selector.select(task, device, candidates)
    d2 = selector.select(task, device, candidates)
    assert d1.selected_object_id == d2.selected_object_id
    assert d1.utility == d2.utility
    assert d1.reasons == d2.reasons
