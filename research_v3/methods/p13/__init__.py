"""P13: Self-regulated learning (SRL) behaviour analysis from OULAD clickstream.

SCOPE GUARD — read before importing anything else here.

OULAD contains no psychological SRL instrument (no MSLQ/OSLQ, no reflection
logs). Every feature produced by this package is a BEHAVIOURAL PROXY with
``construct_validity: "proxy_only"``. This package refuses, at code level, to
emit any artefact that overclaims construct-level SRL evidence: see
``construct_validity.enforce_proxy_guard``, which raises
``ConstructValidityViolation`` whenever a forbidden phrase such as a claim of
direct construct assessment appears in any generated artifact, and
``srl_features.rewrite_measured_srl_claims``, which is used by the report
generator to fail closed.

Design follows the frozen preregistration
``research_v3/experiments/p13/pre_registration.yaml``:
  - features come ONLY from clicks inside the day-0..60 observation window;
  - splits are learner-grouped and presentation-temporal, asserted disjoint;
  - statistics reuse research_v3/eval (splitters, leakage, statistics,
    calibration) — no ad-hoc statistics;
  - descriptive/observational only; causal claims are structurally impossible
    because no intervention exists in the data.
"""
from research_v3.methods.p13.construct_validity import (
    CONSTRUCT_VALIDITY_FLAG,
    ConstructValidityViolation,
    PROXY_ONLY,
    enforce_proxy_guard,
    proxy_only_meta,
)
from research_v3.methods.p13.srl_features import (
    FEATURE_CUTOFF_DAYS,
    FEATURE_CUTOFF_START_DAY,
    SrlFeatureError,
    build_srl_proxy_rows,
    srl_proxy_definitions,
)

__all__ = [
    "CONSTRUCT_VALIDITY_FLAG",
    "PROXY_ONLY",
    "ConstructValidityViolation",
    "enforce_proxy_guard",
    "proxy_only_meta",
    "FEATURE_CUTOFF_DAYS",
    "FEATURE_CUTOFF_START_DAY",
    "SrlFeatureError",
    "build_srl_proxy_rows",
    "srl_proxy_definitions",
]
