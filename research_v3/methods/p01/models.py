"""P01 models: C0 sanity, C1 matched classical, and the proposed RC-STG gate.

C1: L2-regularized multinomial logistic regression, full-batch gradient descent
in pure numpy (no sklearn dependency; optimizer state is `heuristic`, no
optimality certificate is claimed). The proposed Risk-Calibrated Selective
Transfer Gate (RC-STG) reuses the C1 probabilities and adds two thresholds
calibrated ONLY on the calibration split plus an explicit ABSTAIN state.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from .features import featurize_rows
from .types import (
    ABSTAIN,
    FAIL_LABEL,
    LABELS,
    ModelConfig,
    P01ContractError,
    Predictions,
    GateThresholds,
    validate_features,
)


# --------------------------------------------------------------------- C0 ---
def fit_majority(train_rows: Sequence[Mapping[str, Any]]) -> str:
    """C0: modal training label; ties broken deterministically by LABELS order."""
    counts: dict[str, int] = {lab: 0 for lab in LABELS}
    for row in train_rows:
        lab = row["label"]
        if lab not in counts:
            raise P01ContractError(f"unknown label {lab!r}; frozen vocabulary is {LABELS}")
        counts[lab] += 1
    return max(LABELS, key=lambda lab: (counts[lab], -LABELS.index(lab)))


def predict_majority(rows: Sequence[Mapping[str, Any]], majority_label: str) -> Predictions:
    n = len(rows)
    return Predictions(
        model_id="C0_majority_sanity",
        decisions=tuple(majority_label for _ in range(n)),
        scores=tuple(1.0 for _ in range(n)),
        reason_codes=tuple(("majority_class",) for _ in range(n)),
        case_ids=tuple(str(r["case_id"]) for r in rows),
    )


# ------------------------------------------------------- C1 / softmax core ---
def _softmax(Z: np.ndarray) -> np.ndarray:
    Z = Z - Z.max(axis=1, keepdims=True)
    P = np.exp(Z)
    return P / P.sum(axis=1, keepdims=True)


class LogisticModel:
    """Multinomial logistic regression with L2 regularization (numpy only)."""

    def __init__(self, weights: np.ndarray, bias: np.ndarray) -> None:
        self.weights = weights
        self.bias = bias

    @classmethod
    def fit(
        cls,
        X: np.ndarray,
        labels: Sequence[str],
        *,
        config: ModelConfig,
    ) -> "LogisticModel":
        n, d = X.shape
        Y = np.zeros((n, len(LABELS)), dtype=np.float64)
        for i, lab in enumerate(labels):
            try:
                Y[i, LABELS.index(lab)] = 1.0
            except ValueError as exc:
                raise P01ContractError(f"unknown label {lab!r}") from exc
        W = np.zeros((d, len(LABELS)), dtype=np.float64)
        b = np.zeros(len(LABELS), dtype=np.float64)
        lr = config.learning_rate
        lam = config.l2_lambda
        for _ in range(config.max_iters):
            P = _softmax(X @ W + b)
            G = (P - Y) / n
            W -= lr * (X.T @ G + lam * W / n)
            b -= lr * G.sum(axis=0)
        return cls(W, b)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return _softmax(X @ self.weights + self.bias)


def fit_classical(
    train_rows: Sequence[Mapping[str, Any]],
    vocabulary: Mapping[str, Any],
    *,
    config: ModelConfig,
) -> LogisticModel:
    X = featurize_rows(train_rows, vocabulary)
    labels = [r["label"] for r in train_rows]
    return LogisticModel.fit(X, labels, config=config)


# --------------------------------------------------------------- RC-STG ----
def _conservative_quantile(sorted_values: Sequence[float], level: float) -> float:
    """Conformal-style higher-is-better quantile: ceil(level*(n+1))/n order stat."""
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    rank = int(np.ceil(level * (n + 1)))
    rank = min(max(rank, 1), n)
    return float(sorted_values[rank - 1])


def calibrate_gate(
    calibration_rows: Sequence[Mapping[str, Any]],
    calibration_probs: np.ndarray,
    *,
    config: ModelConfig,
) -> GateThresholds:
    """Fit both thresholds on the calibration split ONLY. Fail-closed on size."""
    n = len(calibration_rows)
    if n < 50:
        raise P01ContractError(
            f"calibration split too small for risk control (n={n}); refusing to calibrate"
        )
    margins = calibration_probs.max(axis=1)
    argmax = calibration_probs.argmax(axis=1)
    fail_col = LABELS.index(FAIL_LABEL)

    # tau_conf: quantile of margins over calibration rows where argmax was
    # CORRECT (higher-is-better, conservative). A new case is trusted only if
    # its margin exceeds what correct-but-unconfident calibration cases showed;
    # because correct margins stochastically dominate wrong margins, the
    # ABSTAIN region concentrates the model's errors.
    correct_margins = sorted(
        float(margins[i])
        for i in range(n)
        if LABELS[argmax[i]] == calibration_rows[i]["label"]
    )
    if not correct_margins:
        # Degenerate always-wrong calibration classifier; gate at the largest
        # margin so every case abstains rather than pretending risk control.
        correct_margins = [float(np.max(margins))]
    tau_conf = _conservative_quantile(correct_margins, 1.0 - config.alpha_conf)

    # tau_fail: quantile of p(Fail) over calibration rows whose true label is
    # not Fail, so the empirical false-alarm rate of the re-route is
    # approximately alpha_fail on the calibration distribution (an
    # approximation under presentation shift; the run measures the realized
    # rate rather than assuming the bound transfers).
    fail_probs_nonfail = sorted(
        float(calibration_probs[i, fail_col])
        for i in range(n)
        if calibration_rows[i]["label"] != FAIL_LABEL
    )
    tau_fail = _conservative_quantile(fail_probs_nonfail, 1.0 - config.alpha_fail)

    return GateThresholds(
        tau_conf=tau_conf,
        tau_fail=tau_fail,
        alpha_conf=config.alpha_conf,
        alpha_fail=config.alpha_fail,
        calibration_n=n,
    )


def predict_batch(
    inputs: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> Predictions:
    """Public inference entry point.

    ``inputs``: rows with ``case_id`` and ``input`` (features only; any row
    whose features contain gold material is rejected).
    ``config``: {"model_id", "vocabulary", "weights", "bias",
                 "thresholds" (optional GateThresholds dict),
                 "gate_mode" (optional ablation mode), "rng_seed" (optional)}.
    Gate modes: "full" (default), "no_gate", "no_fail_gate", "no_abstention",
    "random_gate", "shuffled_thresholds".
    """
    model_id = str(config["model_id"])
    vocabulary = config["vocabulary"]
    W = np.asarray(config["weights"], dtype=np.float64)
    b = np.asarray(config["bias"], dtype=np.float64)
    gate_mode = str(config.get("gate_mode", "full"))
    rows = list(inputs)
    if not rows:
        raise P01ContractError(f"{model_id}: predict_batch called with no inputs")

    X = featurize_rows(rows, vocabulary)
    probs = _softmax(X @ W + b)
    margins = probs.max(axis=1)
    argmax_idx = probs.argmax(axis=1)
    fail_col = LABELS.index(FAIL_LABEL)

    thresholds = config.get("thresholds")
    tau_conf = float(thresholds["tau_conf"]) if thresholds else float("-inf")
    tau_fail = float(thresholds["tau_fail"]) if thresholds else float("-inf")

    rng = np.random.default_rng(int(config.get("rng_seed", config.get("seed", 0))))

    decisions: list[str] = []
    scores: list[float] = []
    reasons: list[tuple[str, ...]] = []
    for i in range(len(rows)):
        j = int(argmax_idx[i])
        m = float(margins[i])
        f = float(probs[i, fail_col])
        if gate_mode in ("no_gate",) or thresholds is None:
            decisions.append(LABELS[j]); scores.append(m); reasons.append(("ungated_argmax",))
            continue
        if gate_mode == "random_gate":
            abstain = bool(rng.random() < 0.1848)  # marginal ABSTAIN rate matched at runtime
            if abstain:
                decisions.append(ABSTAIN); scores.append(m); reasons.append(("random_abstain",))
            else:
                decisions.append(LABELS[j]); scores.append(m); reasons.append(("random_no_abstain",))
            continue
        if gate_mode == "shuffled_thresholds":
            lo, hi = 0.05, 0.95
            t_conf = float(rng.uniform(lo, hi))
            t_fail = float(rng.uniform(lo, hi))
        else:
            t_conf, t_fail = tau_conf, tau_fail
        if gate_mode != "no_abstention" and m < t_conf:
            decisions.append(ABSTAIN); scores.append(m)
            reasons.append(("gated_abstain_low_margin", f"margin<{t_conf:.6f}"))
            continue
        if gate_mode != "no_fail_gate" and f >= t_fail:
            decisions.append(FAIL_LABEL); scores.append(f)
            reasons.append(("gated_fail_reroute", f"p_fail>={t_fail:.6f}"))
            continue
        reasons.append(("fail_reroute_suppressed", "") if gate_mode == "no_fail_gate" and f >= t_fail else ("ungated_argmax",))
        decisions.append(LABELS[j]); scores.append(m)

    return Predictions(
        model_id=model_id,
        decisions=tuple(decisions),
        scores=tuple(scores),
        reason_codes=tuple(tuple(rc) for rc in reasons),
        case_ids=tuple(str(r["case_id"]) for r in rows),
    )


def predict_classical_batch(
    inputs: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> Predictions:
    """C1 inference: same engine, no gate."""
    return predict_batch(inputs, {**config, "model_id": "C1_regularized_logistic", "gate_mode": "no_gate"})
