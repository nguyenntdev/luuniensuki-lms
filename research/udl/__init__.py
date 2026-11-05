"""Research Universal Design for Learning (UDL) & Multimodal Equivalence (Study LN-07)."""
from research.udl.modality_equivalence import (
    POLICY_VERSION,
    BASELINE_POLICY_VERSION,
    ABLATION_POLICY_VERSION,
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
