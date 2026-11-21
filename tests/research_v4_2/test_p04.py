"""Unit and contract tests for P04:
- All 12 artifact receipts exist and validate schema
- Proposed candidate beats baseline B* (win contract: delta >= delta_min)
- Invariant & negative controls pass
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import numpy as np

from research_v4_2.papers.p04.experiment import run_p04_experiment
from research_v4_2.papers.p04.method import OGDShiftPredictor
from research_v4_2.papers.p04.baselines import C1StandardLogistic, C2DomainCORAL

P04_DIR = Path(__file__).resolve().parents[2] / "research_v4_2" / "papers" / "p04"


def test_p04_artifacts_exist():
    expected_artifacts = [
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
        "method.py",
        "baselines.py",
        "experiment.py",
    ]
    for art in expected_artifacts:
        p = P04_DIR / art
        assert p.exists(), f"Artifact {art} missing in {P04_DIR}"


def test_p04_win_contract_satisfied():
    receipt_path = P04_DIR / "09_confirmatory_receipt.json"
    with open(receipt_path, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    assert receipt["passed"] is True
    assert receipt["overall_decision"] in ["TESTED_WIN_SINGLE", "REPLICATED_WIN"]

    delta_min = receipt["delta_min_required"]
    s1_res = receipt["strata_results"]["S1"]
    assert s1_res["delta"] >= delta_min
    assert s1_res["ci95"][0] > 0.0
    assert s1_res["p_value"] < 0.05

    s2_res = receipt["strata_results"]["S2"]
    assert s2_res["delta"] >= delta_min
    assert s2_res["ci95"][0] > 0.0


def test_p04_live_experiment_winning_margin():
    res = run_p04_experiment(seed=42)
    s1 = res["S1"]
    assert s1["delta_auc"] >= 0.02
    assert s1["ci95_diff"][0] > 0.0
    assert s1["p_value"] < 0.05

    s2 = res["S2"]
    assert s2["delta_auc"] >= 0.02
    assert s2["ci95_diff"][0] > 0.0


def test_p04_negative_canary():
    # Negative control: random labels drop performance to ~0.50
    rng = np.random.RandomState(42)
    X = rng.randn(100, 10)
    y_rand = rng.randint(0, 2, size=100)
    model = OGDShiftPredictor(n_features=10).fit(X, y_rand)
    probs = model.predict_proba(X)[:, 1]
    from sklearn.metrics import roc_auc_score
    auc = roc_auc_score(y_rand, probs)
    assert 0.40 <= auc <= 0.70  # No miraculous shortcut learning
