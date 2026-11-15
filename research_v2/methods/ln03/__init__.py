"""LN-03 — Evidence-Grounded Dual-Mode Spaced Learning (Research V2 methods).

Modules:
- ``proposed``        : dual-mode scheduler with fact-stability + source gates
- ``baselines``       : B0 always-schedule (sanity) and C1 Leitner 5-box (classical)
- ``ablations``       : A1 no source gate, A2 no fact stability, A3 no due scheduling
- ``legacy_adapter``  : provenance bridge to the observed legacy engine
- ``labels``          : native decision space + typed validation
- ``scenario``        : inference-time feature extraction and typed validation
- ``metrics``         : study-local diagnostics (evaluator-side)

Runner aliases (matrix ``methods`` entries import these directly):
``baselines_b0``, ``baselines_c1``, ``ablations_a1``, ``ablations_a2``, ``ablations_a3``.
"""
from . import (  # noqa: F401
    ablations,
    baselines,
    errors,
    labels,
    legacy_adapter,
    metrics,
    proposed,
    scenario,
)
from .errors import PolicyConfigError, ScenarioError  # noqa: F401
from .labels import STUDY_ID, validate_native_decision  # noqa: F401
from .proposed import METHOD_ID, METHOD_VERSION, predict_batch  # noqa: F401

__all__ = [
    "STUDY_ID",
    "METHOD_ID",
    "METHOD_VERSION",
    "predict_batch",
    "validate_native_decision",
    "ScenarioError",
    "PolicyConfigError",
    "ablations",
    "baselines",
    "errors",
    "labels",
    "legacy_adapter",
    "metrics",
    "proposed",
    "scenario",
]
