# -*- coding: utf-8 -*-
"""Research UDL - Task Modality Guard (Study LN-07 alias module).

Re-exports core modality equivalence policy definitions and functions.
"""

from research.udl.modality_equivalence import (
    ABLATION_POLICY_VERSION,
    BASELINE_POLICY_VERSION,
    POLICY_VERSION,
    DeviceConstraint,
    LearningAffordance,
    MediaVariant,
    ModalityDecision,
    PolicyEvaluationResult,
    evaluate_modality_ablation,
    evaluate_modality_baseline,
    evaluate_modality_intervention,
)

__all__ = [
    "POLICY_VERSION",
    "BASELINE_POLICY_VERSION",
    "ABLATION_POLICY_VERSION",
    "LearningAffordance",
    "MediaVariant",
    "DeviceConstraint",
    "ModalityDecision",
    "PolicyEvaluationResult",
    "evaluate_modality_baseline",
    "evaluate_modality_intervention",
    "evaluate_modality_ablation",
]
