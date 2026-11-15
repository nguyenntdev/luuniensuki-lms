"""P01 typed contracts: predictions, decisions, configs. Fail-closed invariants.

`ABSTAIN` and `NOT_APPLICABLE` are decision values distinct from any class
label, per the paper contract. A Prediction never carries gold material.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# Frozen label vocabulary (order defines class indices everywhere in P01).
LABELS: tuple[str, ...] = ("Distinction", "Fail", "Pass", "Withdrawn")
FAIL_LABEL = "Fail"

# Special decisions, disjoint from LABELS.
ABSTAIN = "ABSTAIN"
NOT_APPLICABLE = "NOT_APPLICABLE"
SPECIAL_DECISIONS = frozenset({ABSTAIN, NOT_APPLICABLE})

GOLD_FORBIDDEN_IN_INPUT = frozenset(
    {"label", "labels", "gold", "gold_label", "final_result", "is_correct",
     "correct", "oracle", "expected_decision", "expected_outcome"}
)


class P01ContractError(ValueError):
    """Raised when a P01 input/output violates its frozen contract."""


def validate_features(features: Mapping[str, Any]) -> None:
    """Reject feature mappings that contain gold or identifier material."""
    leaked = sorted(set(features) & GOLD_FORBIDDEN_IN_INPUT)
    if leaked:
        raise P01ContractError(
            f"gold/identifier material leaked into features: {leaked}"
        )
    for key in ("case_id", "id_student", "group_id", "time_key"):
        if key in features:
            raise P01ContractError(f"identifier {key!r} must not be a feature")


@dataclass(frozen=True)
class Predictions:
    """One model's decisions over a set of case ids."""

    model_id: str
    decisions: tuple[str, ...]
    scores: tuple[float, ...]
    reason_codes: tuple[tuple[str, ...], ...]
    case_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        n = len(self.case_ids)
        if not (n == len(self.decisions) == len(self.scores) == len(self.reason_codes)):
            raise P01ContractError(
                f"{self.model_id}: case_ids/decisions/scores/reason_codes misaligned "
                f"({n}, {len(self.decisions)}, {len(self.scores)}, {len(self.reason_codes)})"
            )
        for d in self.decisions:
            if d not in LABELS and d not in SPECIAL_DECISIONS:
                raise P01ContractError(
                    f"{self.model_id}: decision {d!r} is neither a class label nor a special decision"
                )
        for s in self.scores:
            if not (0.0 <= s <= 1.0):
                raise P01ContractError(f"{self.model_id}: score {s!r} outside [0, 1]")

    def to_jsonl_rows(self) -> list[dict[str, Any]]:
        """Oracle-free rows: no gold material may ever enter a prediction file."""
        rows: list[dict[str, Any]] = []
        for cid, d, s, rc in zip(self.case_ids, self.decisions, self.scores, self.reason_codes):
            rows.append(
                {
                    "case_id": cid,
                    "decision": d,
                    "score": round(float(s), 10),
                    "reason_codes": list(rc),
                    "model_id": self.model_id,
                }
            )
        return rows


@dataclass(frozen=True)
class GateThresholds:
    """Calibrated thresholds; fitted ONLY on the calibration split."""

    tau_conf: float
    tau_fail: float
    alpha_conf: float
    alpha_fail: float
    calibration_n: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tau_conf": self.tau_conf,
            "tau_fail": self.tau_fail,
            "alpha_conf": self.alpha_conf,
            "alpha_fail": self.alpha_fail,
            "calibration_n": self.calibration_n,
        }


@dataclass(frozen=True)
class ModelConfig:
    """Frozen hyperparameters (preregistration.yaml hyperparameters_frozen)."""

    l2_lambda: float = 1.0
    max_iters: int = 250
    learning_rate: float = 0.5
    alpha_conf: float = 0.20
    alpha_fail: float = 0.30
    seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "l2_lambda": self.l2_lambda,
            "max_iters": self.max_iters,
            "learning_rate": self.learning_rate,
            "alpha_conf": self.alpha_conf,
            "alpha_fail": self.alpha_fail,
            "seed": self.seed,
        }
