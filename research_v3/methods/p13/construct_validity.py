"""Construct-validity guard for P13.

The single most important module in P13. OULAD clickstream can never measure
the psychological construct of self-regulated learning (SRL): it records that
a platform was clicked, not why. Every feature is therefore labelled
``construct_validity: "proxy_only"`` and this module enforces, mechanically:

1. every SRL proxy definition ships the flag (see srl_operationalisation.yaml
   and srl_features.srl_proxy_definitions);
2. every generated artifact passes ``enforce_proxy_guard``, which FAILS CLOSED
   if any forbidden phrase ("measured SRL", "SRL measurement", "measures
   self-regulation", causal verbs, ...) appears — so a report claiming a real
   SRL measurement cannot be produced silently;
3. nothing in the pipeline can flip the flag without producing a new,
   explicitly-typed object (``promote_to_measured`` is deliberately not
   provided — there is no code path from proxy to measurement).

Citations for the construct argument:
- Zimmerman, B. J. (2000). Attaining self-regulation: A social cognitive
  perspective. In Boekaerts, Pintrich & Zeidner (Eds.), Handbook of
  Self-Regulation (pp. 13-39). Academic Press.
- Winne, P. H., & Hadwin, A. F. (1998). Studying as self-regulated learning.
  In Hacker, Dunlosky & Graesser (Eds.), Metacognition in Educational Theory
  and Practice (pp. 277-304). Erlbaum.
- Jovanović, J., Gašević, D., Dawson, S., Pardo, A., & Mirriahi, N. (2017).
  Learning analytics to unveil learning strategies: A case study.
  Journal of Learning Analytics, 4(1), 42-64.
  -> "clicks are not uniform indicators of engagement/SRL"; indicator validity
     depends on the activity context.
- Gašević, D., Dawson, S., Rogers, T., & Gasevic, D. (2016). Learning analytics
  should not promote one size fits all. LAK '16.
  -> low-inference metrics (raw counts) have weak construct validity.
"""
from __future__ import annotations

import re
from typing import Any

#: The mandatory flag on every proxy. There is no other value.
PROXY_ONLY = "proxy_only"
CONSTRUCT_VALIDITY_FLAG = "construct_validity"

#: Phrases that must never appear in any P13 artifact, because each would
#: assert that the clickstream measures the SRL psychological construct.
FORBIDDEN_MEASUREMENT_PHRASES: tuple[str, ...] = (
    "measured srl",
    "measures srl",
    "measurement of srl",
    "srl measurement",
    "measured self-regulation",
    "measures self-regulation",
    "measure of self-regulation",
    "self-regulation measurement",
    "measured self-regulated learning",
    "measures self-regulated learning",
    "srl level of the student",
    "student's srl level",
    "true srl",
    "actual srl",
    "validated srl instrument",
    "psychometrically validated",
    "causal effect of srl",
    "srl causes",
    "improves srl",
    "increases srl",
    "srl intervention effect",
    "latent srl construct estimated",
    "srl level increased",
    "srl levels increased",
    "srl increased",
    "srl improved",
)

#: Causal verbs that no observational clickstream study may use.
_FORBIDDEN_CAUSAL_PATTERN = re.compile(
    r"\b(caused|causes|causally (?:improv|increas|reduc|affect|drive\w*)|"
    r"leads? to (?:higher|lower|improved|reduced) srl|"
    r"because (?:of|they) srl)\b",
    re.IGNORECASE,
)


class ConstructValidityViolation(ValueError):
    """Raised when an artifact claims more than a behavioural proxy allows."""


def proxy_only_meta(zimmerman_phase: str, citation: str) -> dict[str, Any]:
    """Standard metadata block every SRL proxy definition must carry."""
    if zimmerman_phase not in {"forethought", "performance", "self_reflection"}:
        raise ConstructValidityViolation(
            f"unknown Zimmerman phase {zimmerman_phase!r} "
            "(Zimmerman 2000 phases: forethought, performance, self_reflection)"
        )
    citation_lowers = citation.lower()
    if not any(
        anchor in citation_lowers
        for anchor in ("zimmerman", "winne", "kizilcec", "jovanovic", "gasevic")
    ):
        raise ConstructValidityViolation(
            "every SRL proxy operationalisation must cite Zimmerman/Winne-Hadwin "
            "or an explicit learning-analytics proxy source (Kizilcec/Jovanovic/"
            "Gasevic)"
        )
    return {
        CONSTRUCT_VALIDITY_FLAG: PROXY_ONLY,
        "measured_construct": None,  # NO construct is measured. Ever.
        "proxy_for_construct": "self-regulated learning (Zimmerman, 2000)",
        "zimmerman_phase": zimmerman_phase,
        "operationalisation_citation": citation,
        "validity_limit": (
            "counts platform events, not cognitive self-regulation; "
            "construct validity is proxy_only by design"
        ),
    }


def scan_for_forbidden_claims(text: str) -> list[str]:
    """Return the list of forbidden phrases found in ``text`` (empty = clean)."""
    lowered = text.lower()
    hits = [phrase for phrase in FORBIDDEN_MEASUREMENT_PHRASES if phrase in lowered]
    if _FORBIDDEN_CAUSAL_PATTERN.search(text):
        hits.append("<causal-claim pattern>")
    return hits


def enforce_proxy_guard(artifact_name: str, text: str) -> str:
    """Fail closed: return ``text`` unchanged unless it overclaims.

    Every artifact P13 writes to disk (reports, tables, model cards, READMEs,
    manuscript sections) passes through here. A single forbidden phrase aborts
    the pipeline with ConstructValidityViolation, so an artifact claiming
    "measured SRL" can never be silently produced.
    """
    hits = scan_for_forbidden_claims(text)
    if hits:
        raise ConstructValidityViolation(
            f"{artifact_name}: construct-validity guard rejected forbidden "
            f"phrase(s) {hits!r}. Clickstream features are proxies with "
            f"construct_validity={PROXY_ONLY!r}; they do not measure SRL and "
            "support no causal claim. Rewrite the artifact honestly."
        )
    return text
