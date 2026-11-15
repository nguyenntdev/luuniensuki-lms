"""LN-09 mechanism-isolating ablations.

Each ablation genuinely changes a code path of the proposed engine via its
config flags, and each is directly sensitive to the removed mechanism:

- ``a1`` (disable_descriptive_fallback): removes the descriptive-only
  fallback certificate for suppression/missing-evidence branches -> the
  missing-logs counterexample family degrades from the explicit
  ``abstain_missing_evidence`` certificate (which states "no deficit may be
  inferred") to a bare ``descriptive_summary_only`` with a
  ``descriptive_only_no_action`` reason code. The explicit abstention
  rationale is the removed mechanism.
- ``a2`` (skip_freshness_check + skip_source_verification): removes the
  freshness and source-verification gates -> stale and unverified-source
  cases flow through to an actionable proposal the proposed method refuses.
- ``a3`` (skip_k_anonymity): removes the k-anonymity privacy threshold ->
  small cohorts (n < 5) receive learner-level recommendations the proposed
  method suppresses to descriptive-only.

All ablations run on identical inputs and budgets as the proposed method
(same batch, same config surface); no difference is manufactured by feeding
different data.
"""
from __future__ import annotations

from typing import Any, Mapping

from research_v2.contracts.types import StudyInput, StudyPrediction

from .engine import evaluate_case

METHOD_VERSION = "v2-ablation-1.0.0"


def _predict_with_flags(
    inputs: list[StudyInput], flags: dict[str, bool], config: dict | Mapping[str, Any] | None
) -> list[StudyPrediction]:
    cfg = dict(config or {})
    for flag, value in flags.items():
        cfg[flag] = value
    return [evaluate_case(inp, cfg) for inp in inputs]


def predict_batch(
    inputs: list[StudyInput], config: dict | Mapping[str, Any] | None = None
) -> list[StudyPrediction]:
    """Default ablation entry point (a1: descriptive-only fallback removal)."""
    return _predict_with_flags(inputs, {"disable_descriptive_fallback": True}, config)
