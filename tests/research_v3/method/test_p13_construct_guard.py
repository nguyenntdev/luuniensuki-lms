"""P13 construct-validity guard: no artifact may claim SRL was measured.

The behavioural rule of the whole paper, enforced in code:
  clickstream proxies (construct_validity=proxy_only) can never be promoted,
  silently or loudly, to a measurement of the SRL psychological construct.
"""
from __future__ import annotations

import pytest

from research_v3.methods.p13.construct_validity import (
    CONSTRUCT_VALIDITY_FLAG,
    PROXY_ONLY,
    ConstructValidityViolation,
    enforce_proxy_guard,
    proxy_only_meta,
    scan_for_forbidden_claims,
)
from research_v3.methods.p13.srl_features import srl_proxy_definitions


def test_every_proxy_definition_carries_proxy_only_flag():
    defs = srl_proxy_definitions()
    assert defs["proxies"], "operationalisation table must define proxies"
    for name, meta in defs["proxies"].items():
        assert meta[CONSTRUCT_VALIDITY_FLAG] == PROXY_ONLY, name
        assert meta["measured_construct"] is None
        assert meta["operationalisation_citation"], name


def test_proxy_only_is_the_only_allowed_flag_value():
    # The flag vocabulary has exactly one value; there is no "measured" state.
    assert PROXY_ONLY == "proxy_only"
    with pytest.raises(ConstructValidityViolation):
        proxy_only_meta("measured", "Zimmerman (2000)")


def test_unknown_zimmerman_phase_rejected():
    with pytest.raises(ConstructValidityViolation):
        proxy_only_meta("precontemplation", "Zimmerman (2000)")


def test_uncited_proxy_rejected():
    with pytest.raises(ConstructValidityViolation):
        proxy_only_meta("forethought", "trust me")


@pytest.mark.parametrize(
    "claim",
    [
        "We measured SRL in OULAD.",
        "The features constitute an SRL measurement of each student.",
        "Our proxy measures self-regulation directly.",
        "Students' SRL level increased because of the intervention.",
        "The latent SRL construct estimated here shows a causal effect of srl.",
        "This instrument is psychometrically validated for SRL.",
    ],
)
def test_any_output_claiming_measured_srl_fails_the_guard(claim: str):
    # THE negative case required by the task: an artifact claiming "measured
    # SRL" cannot be produced; enforce_proxy_guard fails closed.
    with pytest.raises(ConstructValidityViolation):
        enforce_proxy_guard("report.md", claim)
    assert scan_for_forbidden_claims(claim)


def test_causal_language_fails_the_guard():
    with pytest.raises(ConstructValidityViolation):
        enforce_proxy_guard("abstract.md", "Regular study sessions causally improved outcomes; the mechanism caused higher pass rates.")


def test_honest_proxy_wording_passes_the_guard():
    ok = (
        "SRL-proxy features (construct_validity: proxy_only) derived from "
        "OULAD clickstream are behavioural correlates; they do not measure SRL "
        "and no causal claim is made."
    )
    assert enforce_proxy_guard("report.md", ok) == ok


def test_there_is_no_promotion_code_path():
    # Ensure the module exposes no function that upgrades the flag.
    import research_v3.methods.p13.construct_validity as cv

    public = {n for n in dir(cv) if not n.startswith("_")}
    assert not any("promote" in n or "upgrade" in n or "measured" == n for n in public), sorted(public)
