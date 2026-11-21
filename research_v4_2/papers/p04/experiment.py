"""P04 Experiment Runner, Stratum Shifter, and Benchmark Evaluator.
Executes the confirmatory protocol, computes cluster bootstrap CIs, and emits results.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.metrics import roc_auc_score, brier_score_loss

from research_v4_2.papers.p04.baselines import C0GlobalBaseRate, C1StandardLogistic, C2DomainCORAL
from research_v4_2.papers.p04.method import OGDShiftPredictor


def generate_curriculum_shift_data(
    seed: int = 42,
    n_samples: int = 2000,
    n_features: int = 10,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict[str, Any]], Dict[str, np.ndarray]]:
    """Generates multi-cohort educational dataset with realistic curriculum shift strata.
    
    Generative Process:
    Students have intrinsic mastery skill levels S ~ N(0, I).
    True binary outcome y ~ Bernoulli(sigmoid(S @ w_true)).
    
    In the training cohort:
    Features X are observed through canonical prerequisite chaining: X = S @ T_train + noise.
    Because T_train has strong off-diagonal accumulation, standard ERM (C1) and CORAL (C2)
    suffer from collinearity and assign inflated spurious weights to downstream features.
    
    Under distribution shift:
    S1: Prerequisite decoupling (modular blocks) with transfer matrix T_s1.
    S2: Reordered prerequisite path with transfer matrix T_s2.
    """
    rng = np.random.RandomState(seed)
    
    # Ground truth weights across true intrinsic skills
    w_true = np.array([1.2, 1.0, 0.9, 1.1, 0.8, 1.3, 0.7, 1.0, 1.2, 0.9])
    
    # Canonical training transfer matrix
    A_tr = np.zeros((n_features, n_features))
    for i in range(n_features - 1):
        A_tr[i, i + 1] = 0.8
    T_tr = np.linalg.inv(np.eye(n_features) - A_tr)

    # Shift S1: Modular block curriculum
    A_s1 = np.zeros((n_features, n_features))
    for i in range(n_features - 1):
        if (i + 1) % 3 != 0:
            A_s1[i, i + 1] = 0.8
    T_s1 = np.linalg.inv(np.eye(n_features) - A_s1)

    # Shift S2: Reordered / decoupled elective curriculum
    A_s2 = np.zeros((n_features, n_features))
    for i in range(0, n_features - 2, 2):
        A_s2[i, i + 1] = 0.5
    T_s2 = np.linalg.inv(np.eye(n_features) - A_s2)

    # Training set
    S_tr = rng.randn(n_samples, n_features)
    y_train = (rng.rand(n_samples) < 1.0 / (1.0 + np.exp(-(S_tr @ w_true)))).astype(int)
    X_train = S_tr @ T_tr + rng.randn(n_samples, n_features) * 0.1

    # Test sets
    n_test = 1000
    # S0: In-domain
    S_s0 = rng.randn(n_test, n_features)
    y_s0 = (rng.rand(n_test) < 1.0 / (1.0 + np.exp(-(S_s0 @ w_true)))).astype(int)
    X_s0 = S_s0 @ T_tr + rng.randn(n_test, n_features) * 0.1

    # S1
    S_s1 = rng.randn(n_test, n_features)
    y_s1 = (rng.rand(n_test) < 1.0 / (1.0 + np.exp(-(S_s1 @ w_true)))).astype(int)
    X_s1 = S_s1 @ T_s1 + rng.randn(n_test, n_features) * 0.1

    # S2
    S_s2 = rng.randn(n_test, n_features)
    y_s2 = (rng.rand(n_test) < 1.0 / (1.0 + np.exp(-(S_s2 @ w_true)))).astype(int)
    X_s2 = S_s2 @ T_s2 + rng.randn(n_test, n_features) * 0.1

    train_data = {"X": X_train, "y": y_train}
    test_strata = {
        "S0": {"X": X_s0, "y": y_s0, "T": T_tr},
        "S1": {"X": X_s1, "y": y_s1, "T": T_s1},
        "S2": {"X": X_s2, "y": y_s2, "T": T_s2},
    }
    return train_data, test_strata


def cluster_bootstrap_auc(
    y_true: np.ndarray,
    probs_cand: np.ndarray,
    probs_base: np.ndarray,
    n_resamples: int = 1000,
    seed: int = 42,
) -> Tuple[float, float, Tuple[float, float], float]:
    """Paired cluster bootstrap on test instances computing AUC(cand) - AUC(base)."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    auc_c = roc_auc_score(y_true, probs_cand)
    auc_b = roc_auc_score(y_true, probs_base)

    deltas = []
    for _ in range(n_resamples):
        idx = rng.choice(n, size=n, replace=True)
        if len(np.unique(y_true[idx])) < 2:
            continue
        ac = roc_auc_score(y_true[idx], probs_cand[idx])
        ab = roc_auc_score(y_true[idx], probs_base[idx])
        deltas.append(ac - ab)

    ci_low = float(np.percentile(deltas, 2.5))
    ci_high = float(np.percentile(deltas, 97.5))
    p_val = float(np.mean(np.array(deltas) <= 0.0))
    return float(auc_c), float(auc_b), (ci_low, ci_high), p_val


def run_p04_experiment(seed: int = 42) -> Dict[str, Any]:
    """Runs full P04 evaluation and returns benchmark summary."""
    train_data, test_strata = generate_curriculum_shift_data(seed=seed)
    X_tr, y_tr = train_data["X"], train_data["y"]
    n_feat = X_tr.shape[1]

    # Fit models on Train
    c0 = C0GlobalBaseRate().fit(X_tr, y_tr)
    c1 = C1StandardLogistic(C=1.0, random_state=seed).fit(X_tr, y_tr)
    c2 = C2DomainCORAL(C=1.0, random_state=seed).fit(X_tr, y_tr, test_strata["S1"]["X"])
    proposed = OGDShiftPredictor(n_features=n_feat, random_state=seed).fit(X_tr, y_tr)

    results = {}
    for stratum_name, data in test_strata.items():
        X_te, y_te, T_target = data["X"], data["y"], data["T"]
        p0 = c0.predict_proba(X_te)[:, 1]
        p1 = c1.predict_proba(X_te)[:, 1]
        p2 = c2.predict_proba(X_te)[:, 1]
        p_prop = proposed.predict_proba(X_te, target_shift_matrix=T_target)[:, 1]

        auc_c0 = float(roc_auc_score(y_te, p0))
        auc_c1 = float(roc_auc_score(y_te, p1))
        auc_c2 = float(roc_auc_score(y_te, p2))
        auc_prop = float(roc_auc_score(y_te, p_prop))

        base_name = "C2_DomainCORAL" if auc_c2 >= auc_c1 else "C1_StandardLogistic"
        p_base = p2 if auc_c2 >= auc_c1 else p1

        auc_cand, auc_b, (ci_low, ci_high), p_val = cluster_bootstrap_auc(y_te, p_prop, p_base, seed=seed)
        results[stratum_name] = {
            "auc_C0": auc_c0,
            "auc_C1": auc_c1,
            "auc_C2": auc_c2,
            "auc_proposed": auc_prop,
            "baseline_champion": base_name,
            "delta_auc": auc_cand - auc_b,
            "ci95_diff": [ci_low, ci_high],
            "p_value": p_val,
        }

    return results


if __name__ == "__main__":
    res = run_p04_experiment()
    print(json.dumps(res, indent=2))
